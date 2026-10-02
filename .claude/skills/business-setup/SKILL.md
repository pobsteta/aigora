---
name: business-setup
description: Initial business configuration wizard. Runs on first use to configure the AIGORA for your specific business. Use when context/my-business.md is empty, user says "set up my business", "configure", "initialize", or "start fresh".
user-invocable: true
---

# Business Setup Wizard

Configure the entire AIGORA for a specific business through a conversational questionnaire.

## When to Trigger

- `context/my-business.md` contains placeholder text
- User says "set up my business", "configure", "initialize", or "start fresh"
- User wants to reconfigure from scratch

## Process

Run the phases below **conversationally** — ask a batch of questions, wait for answers, then move to the next phase. Do NOT dump all questions at once.

### Phase 1: Your Business

Ask these questions (one batch):

1. What does your business do? (one sentence)
2. Who are your customers? (industry, size, role they talk to)
3. What's your main offer? (service/product, rough price range)
4. Where do most of your leads come from? (referrals, LinkedIn, ads, content, etc.)
5. What's your biggest business challenge right now?

### Phase 2: Your Voice

Ask these questions:

1. How would you describe your communication style? (e.g., direct and no-BS, warm and approachable, technical and precise)
2. Paste a message, email, or post you've written that sounds like "you" — something you'd actually send
3. What words or phrases do you use often?
4. What tone do you NEVER want to sound like? (e.g., corporate, salesy, overly casual)

### Phase 3: Your Tools & Integrations

Ask these questions:

1. What language would you like me to communicate in? (default: French)
2. What timezone are you in? (e.g., America/New_York, Europe/London, Asia/Tokyo)
3. What tools do you use daily? (CRM, email platform, project management, calendar)
2. Do you create content? If so, what platforms? (LinkedIn, YouTube, blog, newsletter, etc.)
3. What tasks do you wish were automated?
4. Do you use kSuite (Infomaniak) for mail, calendar, kDrive or kChat? If yes, offer to connect it now or later with the `ksuite-setup` skill (`docs/KSUITE.md`).
5. (Optional) Do you want the advanced semantic memory? It runs 100% locally (Ollama + Qdrant, no key, nothing leaves the computer) but needs a one-time install. If yes, note the user's preferred name (memory user ID); if no, it's available later, see `docs/MEMORY-UPGRADE.md`

### Phase 4: Your Goals

Ask these questions:

1. What are your top 3 priorities for the next 90 days?
2. What does success look like for this quarter?
3. What tasks drain your energy and you want off your plate?

### Phase 5: Auto-Configure

After collecting all answers:

1. **Write `context/my-business.md`** — Structured business profile from Phase 1 answers. Include: business description, target customer, main offer, lead sources, current challenge.

2. **Write `context/my-voice.md`** — Voice guide from Phase 2 answers. Include: communication style description, sample text, characteristic phrases, anti-patterns (what to avoid).

3. **Update `config/preferences.yaml`** — Set `language`, `timezone`, content platform preferences, and `assistant_name` (if provided) from Phase 3.

4. **Capture stable facts to memory.** Add the durable facts (user preferences from Phase 3, business facts and goals from Phase 4) to Claude Code's native auto-memory (its project memory folder) and add a short curated line or two to `memory/MEMORY.md` so the always-loaded index reflects them. Use the Write tool. See `.claude/rules/memory-protocol.md` for the protocol.

5. **(Optional) Connections and advanced memory** — If the user uses kSuite, hand off to `ksuite-setup` after this wizard. If they want the advanced memory, add `MEM0_USER_ID` to `.env` and walk through `docs/MEMORY-UPGRADE.md`. Otherwise mention both are available later.

6. **Validation test** — Write a 2-sentence introduction of the user's business in their voice. Ask: "Does this sound like you?" If not, refine the voice guide.

7. **Print capabilities** — Show the user what they can now do:
   ```
   You're set up! Here's what you can do now:

   - "Research [company/person/topic]" — Deep research on anything
   - "Write a LinkedIn post about [topic]" — Content in your voice
   - "Prep for my meeting with [person]" — Research + talking points
   - "Help with this email: [paste]" — Triage, draft replies
   - "Add a task: [description]" — Track tasks and projects
   - "Weekly review" — Review your week and plan the next
   - "Create a skill for [workflow]" — Build new reusable workflows
   ```

## Script

Use `scripts/init_business.py` for writing the context files in a consistent format. Pass collected answers as JSON.

## Edge Cases

- If user wants to skip a phase, that's fine — write what you have
- If user gives very short answers, ask one follow-up for the most critical info
- If reconfiguring, back up existing files to `.tmp/` before overwriting
- If user pastes a very long voice sample, extract the key patterns (don't store the full text)
