#!/usr/bin/env node

/**
 * Simple test script to verify Wolf Logic MCP Memory Server functionality
 */

import { MemoryStorage } from '../dist/memory.js';

async function runTests() {
  console.log('🧪 Running Wolf Logic MCP Memory Server Tests...\n');
  
  const storage = new MemoryStorage();
  let passedTests = 0;
  let totalTests = 0;

  // Test 1: Store a memory
  totalTests++;
  console.log('Test 1: Store a memory');
  const id1 = await storage.store(
    'User prefers dark mode',
    'user_preferences',
    { source: 'settings' },
    ['ui', 'theme']
  );
  if (id1) {
    console.log('✅ PASSED - Memory stored with ID:', id1);
    passedTests++;
  } else {
    console.log('❌ FAILED - Could not store memory');
  }

  // Test 2: Retrieve the memory
  totalTests++;
  console.log('\nTest 2: Retrieve memory by ID');
  const memory1 = await storage.retrieve(id1);
  if (memory1 && memory1.content === 'User prefers dark mode') {
    console.log('✅ PASSED - Memory retrieved successfully');
    passedTests++;
  } else {
    console.log('❌ FAILED - Could not retrieve memory or content mismatch');
  }

  // Test 3: Store another memory with same context
  totalTests++;
  console.log('\nTest 3: Store another memory');
  const id2 = await storage.store(
    'User prefers large font size',
    'user_preferences',
    { source: 'settings' },
    ['ui', 'accessibility']
  );
  if (id2) {
    console.log('✅ PASSED - Second memory stored with ID:', id2);
    passedTests++;
  } else {
    console.log('❌ FAILED - Could not store second memory');
  }

  // Test 4: Search by context
  totalTests++;
  console.log('\nTest 4: Search by context');
  const contextResults = await storage.searchByContext('user_preferences', 10);
  if (contextResults.length === 2) {
    console.log('✅ PASSED - Found 2 memories in context');
    passedTests++;
  } else {
    console.log(`❌ FAILED - Expected 2 memories, found ${contextResults.length}`);
  }

  // Test 5: Search by tags
  totalTests++;
  console.log('\nTest 5: Search by tags');
  const tagResults = await storage.searchByTags(['ui'], 10);
  if (tagResults.length === 2) {
    console.log('✅ PASSED - Found 2 memories with tag "ui"');
    passedTests++;
  } else {
    console.log(`❌ FAILED - Expected 2 memories, found ${tagResults.length}`);
  }

  // Test 6: List all memories
  totalTests++;
  console.log('\nTest 6: List all memories');
  const allMemories = await storage.listAll(50);
  if (allMemories.length === 2) {
    console.log('✅ PASSED - Listed all 2 memories');
    passedTests++;
  } else {
    console.log(`❌ FAILED - Expected 2 memories, found ${allMemories.length}`);
  }

  // Test 7: Get statistics
  totalTests++;
  console.log('\nTest 7: Get statistics');
  const stats = storage.getStats();
  if (stats.total === 2 && stats.contexts === 1 && stats.tags === 3) {
    console.log('✅ PASSED - Statistics correct:', stats);
    passedTests++;
  } else {
    console.log('❌ FAILED - Statistics incorrect:', stats);
  }

  // Test 8: Delete a memory
  totalTests++;
  console.log('\nTest 8: Delete a memory');
  const deleted = await storage.delete(id1);
  if (deleted) {
    const afterDelete = await storage.retrieve(id1);
    if (afterDelete === null) {
      console.log('✅ PASSED - Memory deleted successfully');
      passedTests++;
    } else {
      console.log('❌ FAILED - Memory still exists after deletion');
    }
  } else {
    console.log('❌ FAILED - Could not delete memory');
  }

  // Test 9: Verify deletion in stats
  totalTests++;
  console.log('\nTest 9: Verify deletion in statistics');
  const statsAfterDelete = storage.getStats();
  if (statsAfterDelete.total === 1) {
    console.log('✅ PASSED - Statistics updated after deletion:', statsAfterDelete);
    passedTests++;
  } else {
    console.log('❌ FAILED - Statistics not updated:', statsAfterDelete);
  }

  // Test 10: Clear all memories
  totalTests++;
  console.log('\nTest 10: Clear all memories');
  await storage.clear();
  const statsAfterClear = storage.getStats();
  if (statsAfterClear.total === 0) {
    console.log('✅ PASSED - All memories cleared:', statsAfterClear);
    passedTests++;
  } else {
    console.log('❌ FAILED - Memories not cleared:', statsAfterClear);
  }

  // Summary
  console.log('\n' + '='.repeat(50));
  console.log(`Test Results: ${passedTests}/${totalTests} tests passed`);
  console.log('='.repeat(50));
  
  if (passedTests === totalTests) {
    console.log('🎉 All tests passed!');
    process.exit(0);
  } else {
    console.log('⚠️  Some tests failed');
    process.exit(1);
  }
}

runTests().catch((error) => {
  console.error('❌ Test execution failed:', error);
  process.exit(1);
});
