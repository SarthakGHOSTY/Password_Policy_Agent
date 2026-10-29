# Password & Policy Agent

A chat assistant that manages Linux password policy on a simulated server. You type in plain English, a
free open-source model on Groq decides which tool to use, and our own code checks every request before
anything changes.

## Run it

1. Install Python 3.10 or newer. Nothing else is needed.
2. Get a free API key at https://console.groq.com/keys
3. Copy `config.example.py` to `config.py`, then paste the key into `GROQ_API_KEY`.
   `config.py` is git-ignored, so your key stays on your machine.
4. Run `python app.py`. The page opens at http://127.0.0.1:8765

## What you can ask

- **Change settings:** "Make alice's password expire every 30 days", "Lock bob's password"
- **Ask about accounts:** "Which accounts need attention?", "When does alice's password expire?"
- **Learn:** "What does chage -M do?", "What is a good password expiry policy?"
- **Follow-ups:** the agent remembers the last few messages, so "now unlock him" works.

## How a request is handled

```
You type a message
  -> agent.py sends it to the model with the 10 tool descriptions
  -> the model either answers in text, or asks to call a tool
  -> every tool call passes five checks:
       Whitelist  only the 10 tools in tools.py exist
       Validate   real user, whole numbers, valid date, never root or system accounts
       Confirm    locking or disabling an account waits for your approval
       Execute    the command is applied to the simulated /etc/shadow
       Log        every attempt is recorded, including blocked ones
  -> the result goes back to the model, which writes the reply you see
```

The model never writes or runs a command. It can only ask for one of the tools, and the checks are plain
Python, so they work even if the model is tricked by a malicious prompt.

## The files

| File | What it does |
|------|--------------|
| `config.example.py` | Template for `config.py`: the Groq API key, the model list, and the port. Copy it to `config.py` (git-ignored). |
| `accounts.py` | The simulated `/etc/shadow`: six accounts (four regular users, root and daemon) and how each `chage` / `passwd` command changes them. |
| `tools.py` | The 10 tools. Each one validates its input and returns the exact command it would run. Also lists which tools need confirmation. |
| `agent.py` | The system prompt, the call to Groq, and the loop: ask the model, check each tool call, pause for approval, run it, send the result back. Keeps the audit log and short chat memory. |
| `app.py` | A small web server using only the Python standard library. Serves the page and three endpoints: `/api/chat`, `/api/confirm`, `/api/state`. |
| `static/index.html` | Page layout: chat on the left; Accounts, Audit log and Tools tabs on the right. |
| `static/style.css` | The look of the page. |
| `static/app.js` | Sends messages, shows replies and the five-check trace for each tool call, and shows the approval pop-up. |

## The 10 tools

| Tool | Command | Needs approval |
|------|---------|----------------|
| force_password_change | `chage -d 0 <user>` | |
| set_max_days | `chage -M <days> <user>` | |
| set_min_days | `chage -m <days> <user>` | |
| set_warn_days | `chage -W <days> <user>` | |
| set_inactive_days | `chage -I <days> <user>` | |
| set_account_expiry | `chage -E <date> <user>` | yes |
| lock_account | `passwd -l <user>` | yes |
| unlock_account | `passwd -u <user>` | |
| get_password_policy | `chage -l <user>` (read only) | |
| list_accounts | reads every account (read only) | |
