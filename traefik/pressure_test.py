#!/usr/bin/env python3
"""
Traefik Pressure Test - Validate Production Scale Readiness
Tests all Wolf Logic endpoints under load before Friday launch
"""

import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
from datetime import datetime
import json

# Test targets
ENDPOINTS = {
    "api.complexsimplicityai.com": [
        "/api/health",
        "/api/memory-stats",
        "/api/memory/count",
        "/api/namespaces",
    ],
    "hunt.complexsimplicityai.com": [
        "/api/jobs/scraped",
        "/health",
    ],
    "mcp.complexsimplicityai.com": [
        "/health",
        "/mcp/stats",
        "/mcp/tables",
    ],
    "portainer.complexsimplicityai.com": [
        "/",
    ],
    "grafana.complexsimplicityai.com": [
        "/api/health",
    ],
}

# Test configuration
CONCURRENT_USERS = [10, 50, 100, 500, 1000]  # Ramp up
REQUESTS_PER_USER = 100
TIMEOUT = 30

class PressureTest:
    def __init__(self):
        self.results = []
        self.failures = []

    async def fetch(self, session: aiohttp.ClientSession, url: str, user_id: int) -> Dict[str, Any]:
        """Single request with timing"""
        start = time.time()
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as response:
                elapsed = time.time() - start
                return {
                    "url": url,
                    "user": user_id,
                    "status": response.status,
                    "time": elapsed,
                    "success": response.status < 400
                }
        except asyncio.TimeoutError:
            return {
                "url": url,
                "user": user_id,
                "status": 0,
                "time": TIMEOUT,
                "success": False,
                "error": "timeout"
            }
        except Exception as e:
            return {
                "url": url,
                "user": user_id,
                "status": 0,
                "time": time.time() - start,
                "success": False,
                "error": str(e)
            }

    async def user_session(self, user_id: int, urls: List[str]):
        """Simulate single user making requests"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for _ in range(REQUESTS_PER_USER):
                for url in urls:
                    tasks.append(self.fetch(session, url, user_id))

            results = await asyncio.gather(*tasks)
            self.results.extend(results)

    async def run_test(self, concurrent_users: int, urls: List[str]):
        """Run test with N concurrent users"""
        print(f"\n{'='*60}")
        print(f"Testing {concurrent_users} concurrent users")
        print(f"Each user: {REQUESTS_PER_USER} requests")
        print(f"Total requests: {concurrent_users * REQUESTS_PER_USER * len(urls)}")
        print(f"{'='*60}\n")

        self.results = []
        start_time = time.time()

        # Spawn concurrent users
        tasks = [self.user_session(i, urls) for i in range(concurrent_users)]
        await asyncio.gather(*tasks)

        elapsed = time.time() - start_time

        # Analyze results
        self.analyze_results(concurrent_users, elapsed)

    def analyze_results(self, concurrent_users: int, total_time: float):
        """Analyze and print results"""
        total_requests = len(self.results)
        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]

        response_times = [r['time'] for r in successful]

        print(f"Results for {concurrent_users} concurrent users:")
        print(f"  Total Requests: {total_requests}")
        print(f"  Successful: {len(successful)} ({len(successful)/total_requests*100:.1f}%)")
        print(f"  Failed: {len(failed)} ({len(failed)/total_requests*100:.1f}%)")
        print(f"  Total Time: {total_time:.2f}s")
        print(f"  Requests/sec: {total_requests/total_time:.2f}")

        if response_times:
            print(f"\nResponse Times:")
            print(f"  Min: {min(response_times)*1000:.0f}ms")
            print(f"  Max: {max(response_times)*1000:.0f}ms")
            print(f"  Mean: {statistics.mean(response_times)*1000:.0f}ms")
            print(f"  Median: {statistics.median(response_times)*1000:.0f}ms")
            print(f"  p95: {statistics.quantiles(response_times, n=20)[18]*1000:.0f}ms")
            print(f"  p99: {statistics.quantiles(response_times, n=100)[98]*1000:.0f}ms")

        if failed:
            print(f"\nFailure Analysis:")
            error_types = {}
            for f in failed:
                error = f.get('error', f'HTTP {f["status"]}')
                error_types[error] = error_types.get(error, 0) + 1

            for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {error}: {count}")

        # Pass/Fail criteria
        success_rate = len(successful) / total_requests * 100
        avg_response = statistics.mean(response_times) * 1000 if response_times else 9999

        print(f"\n{'='*60}")
        if success_rate >= 99.5 and avg_response < 500:
            print("✓ PASS - Traefik is production ready")
        elif success_rate >= 95 and avg_response < 1000:
            print("⚠ MARGINAL - May need tuning")
        else:
            print("✗ FAIL - Not ready for production")
        print(f"{'='*60}\n")

        return {
            "concurrent_users": concurrent_users,
            "total_requests": total_requests,
            "success_rate": success_rate,
            "avg_response_ms": avg_response,
            "total_time": total_time,
            "requests_per_sec": total_requests/total_time
        }

async def main():
    """Run full pressure test suite"""
    print("\n🐺 Wolf Logic - Traefik Pressure Test")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Build full URL list
    urls = []
    for domain, paths in ENDPOINTS.items():
        for path in paths:
            urls.append(f"https://{domain}{path}")

    print(f"Testing {len(urls)} endpoints:")
    for url in urls:
        print(f"  - {url}")

    test = PressureTest()
    summary = []

    # Ramp up test
    for concurrent_users in CONCURRENT_USERS:
        result = await test.run_test(concurrent_users, urls)
        summary.append(result)

        # Cool down between tests
        await asyncio.sleep(5)

    # Final summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"{'Users':<10} {'Requests':<12} {'Success%':<12} {'Avg ms':<12} {'Req/sec':<12}")
    print("-"*60)

    for s in summary:
        print(f"{s['concurrent_users']:<10} {s['total_requests']:<12} "
              f"{s['success_rate']:<12.1f} {s['avg_response_ms']:<12.0f} "
              f"{s['requests_per_sec']:<12.1f}")

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'/tmp/pressure_test_{timestamp}.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\nResults saved to: /tmp/pressure_test_{timestamp}.json")
    print(f"\n{'='*60}")
    print("If Traefik passes this test, we launch Friday. 🚀")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(main())
