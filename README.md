# Verify

**Stop misinformation before it spreads. Verify claims directly on social media.**

Verify is a browser extension that adds fact-checking to scoial media. With a single click, get instant verification results for any claim along with sources.

---

## What It Does

Hover over any post and hit **Verify**. Within seconds, you'll see:
- ✅ **Claims entailed** by credible sources
- ❌ **Claims refuted** with contradicting evidence  
- ⚠️ **Unclear claims** flagged for further investigation

All results appear right on the post.

---

## In Action

### Catching False Claims

![Verify catching misinformation](/examples/refute.png)

*A user verifies a claim. Verify surfaces sources that directly contradict it.*

### Confirming Accurate Information

![Verify confirming facts](/examples/support.png)

*A claim gets verified against multiple reliable sources.*

### When Facts Are Complicated

![Verify handling nuance](/examples/support_and_refute.png)

*Some claims aren't black and white. Verify shows you the nuance.*

---

## The Sites we Search and Exclude
Verify searches a wide range of reputable sources to ensure accurate verification. However, it excludes certain sites known for unreliable information.
### Sites We Search
- FactCheck.org
- Snopes
- PolitiFact
- Reuters Fact Check
- Wikipedia (with caution)
- Reputable news outlets (BBC, CNN, The New York Times)

### Sites We Exclude
- The Onion (satirical content)
- x.com (Formally Twitter)
- reddit.com (user-generated content)
- theguardian.com (due to frequent opinion pieces)
- foxnews.com (due to known biases)

## Install

1. **Clone this repo**
   ```bash
   git clone https://github.com/EunoiaC/verify.git
   cd verify
   ```

2. **Set up your API keys** — Create a `.env` file in the root directory:
   ```
   GEMINI_API=your_gemini_key_here
   GOOGLE_SEARCH_API=your_google_search_key_here
   ```

3. **Load into Chrome**
   - Open `chrome://extensions`
   - Enable **Developer mode** (top right)
   - Click **Load unpacked**
   - Select the `chrome_extension` folder

4. Navigate to Reddit and look for the Verify button

---

## How It Works

- A finetuned gemini-2.5-flash model processes the social media post to extract the main claims.
- Using the Google Custom Search API, Verify searches for relevant fact-checking articles from reputable sources.
- An embedding model compares the claims against the retrieved articles to determine which parts of the documents are relevant.
- Once we built the context, a deberta model finetuned on nli tasks classifies each claim as **entails**, **contradicts**, or **neutral** based on the evidence.
---

## Support

Found a bug? Have feedback? [Open an issue](https://github.com/EunoiaC/verify/issues)

---

*Verify: Because social media deserves better information.*
