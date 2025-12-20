# Beta Recruitment Templates - Complex Logic

**DO NOT POST THESE UNTIL WOLF GIVES APPROVAL**

---

## Reddit Post Template - r/betatests

**Title:** `[Android] Complex Logic - AI Job Search with 2,916 Pre-Scraped Remote Jobs`

**Body:**
```
Recruiting beta testers for Complex Logic, an AI-powered job search Android app.

**What it does:**
- 2,916 pre-scraped remote jobs (ZipRecruiter, Indeed, LinkedIn)
- AI generates tailored resumes for each application
- Local-first architecture (your data stays on your phone)
- Full offline mode with smart sync
- Built-in metrics to track your job search effectiveness

**What I'm testing:**
- User onboarding flow
- AI resume generation quality
- Offline sync reliability
- Overall UX/UI feedback

**Requirements:**
- Android 7.0+ (API 24)
- Willing to provide feedback via survey or GitHub issues
- Active job seeker preferred (but not required)

**Beta perks:**
- Early access to all premium features (free during beta)
- Direct input on feature development
- Credits toward premium subscription when we launch

**Privacy:** Local-first means your job search data stays on your device unless you explicitly sync.

Interested? Sign up here: [Google Form link - INSERT WHEN READY]

Launching on Play Store soon - be one of the first!
```

---

## Reddit Post Template - r/androidapps

**Title:** `[Beta] Complex Logic - AI Job Search App with Local-First Privacy`

**Body:**
```
Hey r/androidapps!

Recruiting beta testers for Complex Logic, an AI job search app built with privacy in mind.

**What's different:**
- 2,916 pre-scraped remote jobs (no tracking your searches)
- AI tailors resumes for each application
- Local-first: your data stays on YOUR phone
- Works fully offline, syncs when you want
- Built-in AI metrics to understand your job search patterns

**Beta perks:**
- All premium features free during beta
- Shape the product roadmap with your feedback
- Premium credits when we launch

**Requirements:**
- Android 7.0+
- Provide feedback (survey/GitHub)
- Job seekers preferred

**Privacy focus:** We don't track you. Everything runs locally. Your applications, resumes, cover letters - all stored on your device.

Sign up: [Google Form link - INSERT WHEN READY]

Play Store launch coming soon.

Questions? Reach out at ai-memory@complexsimplicityai.com
```

---

## Google Form Questions (Ready to Build)

**Section 1: Contact Info**
- Email address (required)
- Android device model (required)
- Android version (required)

**Section 2: Job Search Context**
- Are you currently job searching? (Yes / No / Casually browsing)
- What industries are you targeting? (Multiple choice + Other)
- How many job applications do you submit per week? (0-5 / 6-10 / 11-20 / 20+)

**Section 3: Tech Comfort**
- How comfortable are you with beta software? (Very / Somewhat / Not very)
- Would you be willing to provide detailed feedback? (Yes / Maybe / No)
- Preferred feedback method? (Survey / GitHub issues / Email / Discord)

**Section 4: Privacy & Consent**
- I understand this is beta software and may have bugs (Checkbox)
- I consent to providing feedback on my experience (Checkbox)
- I'm interested in premium features when launched (Optional checkbox)

---

## Ionos AI Email Auto-Response Template

**Subject:** Welcome to Complex Logic Beta Testing!

**Body:**
```
Hey [Name],

Thanks for signing up to beta test Complex Logic!

Here's what happens next:

1. **Download the APK** (link coming in 24-48 hours)
2. **Install on your Android device** (Android 7.0+)
3. **Use it for your job search** for at least 1 week
4. **Share feedback** via our survey or GitHub

**What you get:**
- Free access to all premium features during beta
- Direct line to the dev team (that's me!)
- Credits toward premium when we launch

**Privacy reminder:** Your data stays on your phone. We don't track you or sell your info.

Questions? Just reply to this email.

Let's find you a job,
Wolf
Complex Logic Team

ai-memory@complexsimplicityai.com
```

---

## Grafana Dashboard Config (Metrics to Track)

**Beta Signup Metrics:**
- Total signups (from Google Form → beta_prospects table)
- Signups by source (Reddit, LinkedIn, Product Hunt, etc.)
- Conversion rate (signups → actual testers)
- Feedback submission rate

**SQL Query for Grafana:**
```sql
-- Total signups by source
SELECT source, COUNT(*) as signups
FROM beta_prospects
WHERE outreach_status IN ('contacted', 'signed_up')
GROUP BY source
ORDER BY signups DESC;

-- Signup velocity (daily)
SELECT DATE(created_at) as date, COUNT(*) as signups
FROM beta_prospects
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date;

-- Conversion funnel
SELECT 
    COUNT(*) FILTER (WHERE outreach_status = 'pending') as pending,
    COUNT(*) FILTER (WHERE outreach_status = 'contacted') as contacted,
    COUNT(*) FILTER (WHERE outreach_status = 'signed_up') as signed_up
FROM beta_prospects;
```

---

**STATUS: All templates ready. Awaiting Wolf's approval to execute.**
