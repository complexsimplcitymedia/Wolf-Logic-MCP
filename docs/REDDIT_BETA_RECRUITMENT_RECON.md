# Reddit API Beta Tester Recruitment - Reconnaissance Report

**Date**: 2025-12-16
**Purpose**: Research Reddit API capabilities for Wolf Hunt Android app beta recruitment
**Status**: RECONNAISSANCE ONLY - No posting yet

---

## Executive Summary

Reddit API is operational in 2025 and can be used for automated beta tester recruitment. Facebook Groups API was killed in April 2024, making Reddit the best alternative for automated recruitment.

**Key Finding**: Reddit still allows API posting to subreddits - you can automate this.

---

## Target Subreddits for Beta Testers

### Primary Targets
- **r/beta** - 350K+ beta testers (largest community)
- **r/betatests** - Dedicated beta testing community
- **r/TestMyApp** - Mobile app testing
- **r/alphaandbetausers** - Early access users
- **r/androidapps** - Android app enthusiasts

### Secondary Targets
- **r/Android** - 7M+ Android users (strict posting rules)
- **r/androiddev** - Android developers (may provide quality feedback)
- **r/SideProject** - Indie developers and early adopters

### Success Rate
- Only 1 in 5 beta testers will actually test and provide feedback
- Need minimum 100-300 testers for proper coverage
- Expect 500+ signups to get 100+ active testers

---

## Reddit API Technical Details

### Authentication (OAuth 2.0 Required)
1. Create Reddit app at: https://www.reddit.com/prefs/apps
2. Get credentials:
   - Client ID
   - Client Secret
   - User Agent (must be unique and descriptive)
3. OAuth flow: Authorization → Token → API calls

**User-Agent Format Required**:
```
<platform>:<app_id>:<version> (by /u/<reddit username>)
Example: android:com.complexsimplicityai.wolfhunt:1.0.0 (by /u/YourUsername)
```

### Rate Limits
- **OAuth authenticated**: 100 queries per minute (QPM)
- **Averaged over**: 10-minute window (allows bursts)
- **Unauthenticated**: 10 QPM (mostly blocked now)

**Headers to Monitor**:
- `X-Ratelimit-Used` - Requests used
- `X-Ratelimit-Remaining` - Requests left
- `X-Ratelimit-Reset` - Seconds until reset

### Pricing
- **Free Tier**: Non-commercial use, up to 100 QPM
- **Paid Tier**: $0.24 per 1,000 API calls for commercial use
- **Your use case**: Likely qualifies as free (beta recruitment is non-commercial)

---

## Posting Capabilities

### What You Can Do
- Submit text posts to subreddits
- Submit link posts (to signup form)
- Submit image posts (screenshots)
- Reply to comments
- Edit/delete your posts
- Schedule posts (with cron/automation)

### Post Submission Endpoint
```
POST /api/submit
Parameters:
- sr: subreddit name
- kind: link/self/image
- title: post title
- text: post body (for text posts)
- url: link URL (for link posts)
```

### Example Beta Recruitment Post (Text)
```
Title: [Beta Testers Needed] Wolf Hunt - AI-Powered Job Search Android App

Body:
Hey r/androidapps!

I'm recruiting beta testers for Wolf Hunt, an AI-powered job search app that helps you track applications, generate tailored resumes, and discover remote opportunities.

**What's different:**
- 2,916 pre-scraped jobs (ZipRecruiter, Indeed, LinkedIn, etc.)
- AI-powered resume generation for each application
- Local-first architecture (your data stays on your phone)
- Full offline mode with context-driven sync

**Beta perks:**
- Early access to all premium features (free during beta)
- Direct input on feature development
- Credits toward premium when we launch

**Requirements:**
- Android 7.0+ (API 24)
- Willing to provide feedback via survey or GitHub issues
- Active job seeker preferred (but not required)

**Privacy:** We don't track you. Local-first means your job search data never hits our servers unless you explicitly sync.

Interested? Comment or DM for TestFlight access.

Launching on Play Store this Friday (2025-12-20) - be one of the first!
```

---

## Subreddit Rules Check (Critical)

### r/androidapps Rules
- No spam or self-promotion without contribution
- Must be meaningful participation in community first
- Beta posts allowed but must provide value
- Include [Beta] tag in title
- Respond to all comments within 24 hours

### r/betatests Rules
- Must use [Android] tag
- Include: What it does, what you're testing, requirements
- Provide feedback mechanism (survey/form)
- No payment/compensation allowed (breaks TOS)

### r/beta Rules
- Mostly for Reddit's own beta program
- Third-party betas sometimes allowed
- Check moderator approval first

**Recommendation**: Post to r/androidapps and r/betatests simultaneously. Avoid r/Android (too strict, will remove).

---

## Python Reddit API (PRAW)

### Installation
```bash
pip install praw
```

### Example Code
```python
import praw

# Initialize Reddit client
reddit = praw.Reddit(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    user_agent="android:com.complexsimplicityai.wolfhunt:1.0.0 (by /u/YourUsername)",
    username="YourUsername",
    password="YourPassword"
)

# Submit post to r/androidapps
subreddit = reddit.subreddit("androidapps")
post = subreddit.submit(
    title="[Beta Testers Needed] Wolf Hunt - AI-Powered Job Search",
    selftext="""
    Hey r/androidapps!

    I'm recruiting beta testers for Wolf Hunt...
    [Full post text here]
    """,
    flair_id=None,  # Optional: Add flair if subreddit requires it
    send_replies=True  # Get notifications for comments
)

print(f"Posted: {post.url}")
```

---

## Alternative: Reddit Form Integration

Instead of collecting signups in comments, use a signup form:

**Google Form / Typeform**:
- Name
- Email
- Android version
- Phone model
- Why interested in beta testing?
- Agree to NDA (if needed)

**Post Format**:
```
Title: [Beta] Wolf Hunt - AI Job Search App

Body:
[Brief description]

Sign up here: https://forms.gle/YOUR_FORM_ID

We'll send APK download links via email within 24 hours.
```

---

## Complementary Channels (Not API-Based)

### Twitter/X Hashtags
- #betatesting
- #betatesters
- #testmyapp
- #indiedev
- #androiddev
- #mobileapptesting

### Product Hunt
- Launch as "Coming Soon" with beta signup
- Gets visibility from tech-savvy early adopters

### Indie Hackers
- Post in "Show IH" section
- Community of builders who love testing new products

---

## Risk Assessment

### Low Risk
- Reddit API is stable and well-documented
- Free tier sufficient for beta recruitment
- Active moderation prevents spam flags (if done right)

### Medium Risk
- Subreddit rules can be strict (read carefully)
- Posts may be removed if seen as spam
- Need to respond to all comments or face backlash

### High Risk
- Account ban if violating rules repeatedly
- Shadow ban if User-Agent not unique
- Rate limit if exceeding 100 QPM

**Mitigation**: Post manually first to test community response, then automate if positive.

---

## Recommended Approach

### Phase 1: Manual Reconnaissance (Today)
1. Create throwaway Reddit account (or use existing)
2. Manually post to r/betatests first (lowest risk)
3. Monitor response for 24 hours
4. Engage with all comments

### Phase 2: Targeted Posting (If Phase 1 succeeds)
1. Post to r/androidapps with [Beta] tag
2. Post to r/alphaandbetausers
3. Use signup form to collect testers
4. Target: 500+ signups

### Phase 3: Automation (Optional)
1. Set up PRAW with OAuth
2. Create posting script
3. Schedule posts to multiple subreddits (with delays to avoid spam detection)
4. Auto-respond to common questions

---

## Reddit API Setup Checklist

- [ ] Create Reddit account (if needed)
- [ ] Register app at reddit.com/prefs/apps
- [ ] Get Client ID and Secret
- [ ] Install PRAW (`pip install praw`)
- [ ] Write unique User-Agent string
- [ ] Test authentication with simple API call
- [ ] Read target subreddit rules thoroughly
- [ ] Draft beta recruitment post
- [ ] Create signup form (Google Forms/Typeform)
- [ ] Test post in r/test first
- [ ] Submit to r/betatests
- [ ] Monitor and respond to comments

---

## Estimated Timeline

- **Setup**: 30 minutes (app registration, PRAW install)
- **Post drafting**: 1 hour (multiple subreddits)
- **Manual posting**: 15 minutes
- **Monitoring/responses**: 2-4 hours over 48 hours
- **Tester onboarding**: 1-2 days (email APK links)

**Total**: 3-4 days from post to first testers using app

---

## Cost Analysis

**Reddit API**: $0 (free tier sufficient)
**Form service**: $0 (Google Forms free)
**Email distribution**: $0 (Gmail/SendGrid free tier)
**Total cost**: $0

---

## Alternative If Reddit Fails

1. **TestFlight** (iOS equivalent for Android is Google Play Console Beta)
2. **BetaList** (paid submission: $299)
3. **Product Hunt** (free but competitive)
4. **Indie Hackers** (free, smaller audience)
5. **Direct outreach** to job search influencers on LinkedIn

---

## Sources

- [Reddit Data API Wiki](https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki)
- [Reddit API Limits](https://data365.co/blog/reddit-api-limits)
- [Reddit API: Features, Pricing & Set-ups](https://apidog.com/blog/reddit-api-guide/)
- [How to Find Early Beta Users For Your App](https://www.apptamin.com/blog/find-app-beta-users/)
- [Developer Platform & Accessing Reddit Data](https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data)

---

## Next Steps (Awaiting Wolf's Approval)

1. **Create Reddit app** and get credentials
2. **Draft beta recruitment post** tailored to each subreddit
3. **Set up signup form** for tester collection
4. **Manual test post** to r/betatests
5. **Monitor response** and iterate

**NO POSTING YET - Reconnaissance complete.**

---

**Wolf Hunt Beta Recruitment - Reddit is ready when you are.**

"Today we go scale." - Wolf, 2025-12-16
