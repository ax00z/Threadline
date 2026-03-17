#!/usr/bin/env python3
"""Generate realistic investigative test data in all three formats.

Creates conversations spanning months with:
- Multiple distinct personas with consistent speech patterns
- Realistic message cadences (bursts of activity, quiet periods, off-hours)
- Entities: phone numbers, crypto addresses, coordinates, money amounts, emails
- Multi-line messages, media attachments, system events
- Enough volume to stress-test the UI (~500-2000 messages per file)
"""

import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

OUT_DIR = Path(__file__).parent.parent / "test_data"
OUT_DIR.mkdir(exist_ok=True)

# ── Personas ──────────────────────────────────────────────────────────

WHATSAPP_PERSONAS = {
    "Marco Reyes": {
        "style": "terse",
        "role": "organizer",
        "msgs": [
            "Meeting at the usual spot. 8pm sharp.",
            "Nobody talks on an open line about the shipment.",
            "I told you to use Signal. Delete this thread after reading.",
            "The warehouse on 4th and King is compromised. Use the fallback.",
            "New burner: +1 (347) 555-0188. Only use it for emergencies.",
            "Package arrives Thursday. 14kg. Don't ask questions.",
            "Wire $45,000 to the holding company by EOD.",
            "Who gave Santos my address? I need a name.",
            "Everyone goes dark for 72 hours. No exceptions.",
            "Confirmation code: ECHO-BRAVO-7742",
            "I don't care what he said. The deal is off.",
            "Get me a clean vehicle. Nothing registered to anyone we know.",
            "The lawyer says we're fine but I don't trust lawyers.",
            "Check the IBAN: DE89370400440532013000",
            "Moving operations to the secondary location effective immediately.",
            "Tell Lucia to bring the documents. All of them.",
            "We need to talk. Face to face. No phones.",
            "The accountant found a $12,500 discrepancy. Explain.",
            "GPS coordinates for the drop: 40.7128° N, 74.0060° W",
            "I'm switching to the Canadian line: +1 (416) 555-9031",
            "Nobody leaves town until this is resolved.",
            "Payment confirmed. $78,000 cleared.",
            "Destroy the laptop. Use thermite if you have to.",
            "Meeting moved to Sunday. Same place.",
            "The contact in Zurich wants 15% instead of 10%. Thoughts?",
        ],
    },
    "Lucia Varga": {
        "style": "detailed",
        "role": "logistics",
        "msgs": [
            "I've arranged transport through the Rotterdam port. Container ID: MSKU-7784521. ETA is March 15th, assuming no customs delays.",
            "The documents are ready. Notarized copies of everything including the shell company registration in Cyprus.",
            "Flight booked: AC 847, Toronto → Zurich, departing 06:45 on the 22nd. Seat 4A.",
            "The storage unit at 1847 Industrial Blvd is paid through June. Code is 4491#.",
            "I found us a clean accountant. Her name is Dr. Sarah Chen, she works out of the financial district. Email: s.chen@privateconsult.ch",
            "Shipping manifest attached. 3 pallets, declared as medical equipment. Weight: 340kg total.",
            "The rental property at 55 Harbord St is ready. Keys with the building manager, ask for Mr. Patterson.",
            "I've set up three new accounts:\n- Cayman: KY-8834-2201\n- Swiss: CH93-0076-2011-6238-5295-7\n- Dubai: AE07-0331-0001-9101-0302-001",
            "Our contact in Rotterdam says port security has increased inspections. Suggest we delay by one week.",
            "Budget update:\n- Transport: $34,000\n- Storage: $8,200\n- Documentation: $12,500\n- Contingency: $15,000\nTotal: $69,700",
            "The vehicle is a white 2024 Transit van, plate BXKR 441. Parked at level 3 of the Dundas garage.",
            "Marco, the Zurich meeting is confirmed for March 3rd at 2pm. Hotel Baur au Lac, private dining room.",
            "I need everyone's passport photos by Friday. No excuses.",
            "Picked up the hardware. 3x encrypted phones, 2x laptops (Tails OS), 1x portable shredder.",
            "The real estate agent is getting suspicious. We should slow down the property acquisitions.",
            "Fuel costs are up 22% since January. Adjusting the quarterly budget.",
            "New email for secure comms: ghostwriter@proton.me",
            "The warehouse lease expires April 30. Should I renew or find something new?",
            "Coordinates for the alternate meeting point: 43.6532° N, 79.3832° W (waterfront area)",
            "Everything is packed and ready. Waiting on Marco's go signal.",
        ],
    },
    "Danny Kowalski": {
        "style": "casual",
        "role": "enforcer",
        "msgs": [
            "yo im outside. where u at",
            "that dude from last week is asking questions again. want me to handle it?",
            "lmao santos is so paranoid he changed his burner AGAIN. new number: +1 (917) 555-0244",
            "picked up the package. all good. heading to the warehouse now",
            "bro this traffic on the 401 is killing me. gonna be late",
            "i swept the office for bugs. clean. but found a weird USB drive behind the desk??",
            "u seen the news? feds raided a spot on queen street. not ours but still",
            "need more cash for the week. the guys are getting antsy about pay",
            "alright im going dark for a bit. dont call unless its life or death",
            "just talked to patel. he says the shipment cleared customs no problem",
            "who tf is following lucia? silver honda civic, plate CXRE 992",
            "the new guy checks out. ex-military, no record, solid references",
            "i left $25,000 in the safe at the loft. combo is 28-41-07",
            "marco wants us at the docks by 5am tomorrow. bring the van",
            "someone keyed my car. probably nothing but keeping my eyes open",
            "the gym on college street is a good front. owner is cooperative",
            "cant make the meeting tuesday. dentist appointment lol",
            "santos owes us $4,200 from the last job. im collecting tomorrow",
            "ran into an old contact. says he can get us clean plates for $500 each",
            "everything quiet on my end. too quiet tbh",
        ],
    },
    "+1 (647) 555-0177": {
        "style": "nervous",
        "role": "informant",
        "msgs": [
            "I shouldn't be talking to you but you need to know they're watching the warehouse.",
            "Detective Morrison asked about the shell company yesterday. I played dumb.",
            "I can't do this anymore. The pressure is too much.",
            "There's a new task force. They call it Project Thunderbird. They have wiretaps.",
            "Meet me at the Tim Hortons on Bloor. Come alone. 3pm.",
            "I overheard them mention a CI. Someone on the inside is talking.",
            "My handler wants more. They're threatening to pull my immunity deal.",
            "The surveillance van parks on Dundas every Tuesday and Thursday. Silver Sprinter.",
            "They know about the Zurich connection. I don't know how.",
            "I need $10,000 by Friday or I'm out. Wire it to interac email: safeport@inbox.com",
            "Don't call this number again after tonight. I'm getting a new one.",
            "They have photos of Danny at the warehouse. Timestamp was Feb 14th.",
            "The judge signed off on the production order. Your bank records for the last 2 years.",
            "I'm scared. If they find out I'm talking to both sides I'm dead.",
            "Last update: the raid is planned for sometime in April. I don't have an exact date.",
        ],
    },
    "Santos Rivera": {
        "style": "paranoid",
        "role": "money",
        "msgs": [
            "Switching phones again. Don't save this number.",
            "The crypto wallet is showing weird transactions. Someone skimming?\nBTC address: bc1q42lja79elem0anu8q860g3ez684rfo5p7luvft",
            "I routed the payment through 4 intermediaries. Can't be traced.",
            "Who accessed the offshore account at 3am? I got an alert.",
            "The $120,000 is clean and sitting in the Cayman account.",
            "Using a VPN through Estonia → Singapore → Brazil. IP should show as 177.54.12.89",
            "The ETH wallet has 47.3 ETH. Current value approximately $142,000.\nETH: 0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
            "I found a transaction I didn't authorize. $8,750 to an unknown account. Investigating.",
            "New dead drop for documents: locker 447 at Union Station. Combo: 1-8-3-7",
            "Tell Marco the money printer is working overtime. $500k moved this quarter.",
            "Someone tried to brute force the wallet. 47 failed attempts from a Russian IP.",
            "The Monero is safer. Moving everything over.\nXMR: 44AFFq5kSiGBoZ4NMDwYtN18obc8AemS33DBLWs3H7otXft3XjrpDtQGv7SqSsaBYBb98uNbr2VBBEt7f2wfn3RVGQBEP3A",
            "My accountant in Grand Cayman says the audit is routine. But still.",
            "I built a spreadsheet tracking every dollar. Encrypted on the laptop. Password is offline.",
            "The invoice from the front company is ready. $34,000 for consulting services. Classic.",
        ],
    },
    "Dr. Patel": {
        "style": "professional",
        "role": "facilitator",
        "msgs": [
            "The customs paperwork is in order. I've signed off on the health certificates.",
            "My contact at the port authority confirms the container will not be inspected.",
            "I must stress the importance of maintaining appearances. Any irregularity draws attention.",
            "The laboratory results are ready for collection. Reference number: LAB-2025-4471.",
            "I've arranged a meeting with the import/export board. Purely routine, nothing to worry about.",
            "Please ensure all shipments are labeled correctly. The last batch had discrepancies.",
            "My fee for this quarter is $22,000. Non-negotiable.",
            "The medical supply chain provides excellent cover. I suggest we expand.",
            "I have concerns about the new personnel. Background checks are essential.",
            "The WHO inspection passed without issue. Our documentation is impeccable.",
            "Conference in Geneva next month. Good opportunity to meet our European partners.",
            "I've updated the compliance reports. Everything appears legitimate on paper.",
            "Recommend we reduce shipment frequency. Three per month is drawing patterns.",
            "The pharmaceutical license renewal is approved through 2027.",
            "Final note: the temperature-controlled container costs an additional $4,500 per shipment.",
        ],
    },
    "+44 7700 900123": {
        "style": "terse",
        "role": "overseas",
        "msgs": [
            "London end is sorted. Goods arriving at Felixstowe.",
            "Price increase. £85 per unit. Take it or leave it.",
            "My people in Manchester confirm delivery. All accounted for.",
            "Wire the balance to Barclays sort code 20-45-12, account 73849201.",
            "New passport arrived. Clean as a whistle.",
            "The flat in Canary Wharf is ready. Furnished, no paper trail.",
            "Eurostar to Brussels on the 15th. Meeting the Belgian contact.",
            "Lost contact with our man in Amsterdam. Not answering for 48 hours.",
            "Security at Heathrow has tightened. Using private airfield from now on.",
            "£150,000 transferred. Confirm receipt.",
            "Don't contact me on weekends. I have a family.",
            "The solicitor reviewed the contracts. All ironclad.",
        ],
    },
}

TELEGRAM_PERSONAS = {
    "CyberVault": {
        "msgs": [
            "Deploying the new payload to staging. SHA-256: a1b2c3d4e5f6789012345678abcdef0123456789abcdef0123456789abcdef01",
            "The C2 server is migrated to 185.220.101.42. All nodes should reconnect within 6 hours.",
            "Patch notes for v3.7:\n- Fixed memory leak in persistence module\n- Added polymorphic engine\n- Improved evasion against EDR solutions\n- New exfiltration channel via DNS tunneling",
            "Everyone needs to rotate their PGP keys. The old batch is compromised.\nNew fingerprint: 4E1F 799A A4FF 2279 EE52 4FFF 2A3C D011 B4D9 7A4E",
            "Ransomware deployment window: 2am-4am UTC on Saturday. All teams standby.",
            "The phishing campaign hit a 34% click rate. Better than expected.",
            "Wallet check: 12.7 BTC across 4 wallets. Tumbling starts tonight.",
            "If anyone gets burned, activate the dead man's switch. No exceptions.",
            "New zero-day in Microsoft Exchange. CVE pending. We have 72 hours before patch.",
            "Tor hidden service is up: http://threadlinexxxxxxx.onion (not a real address)",
            "We intercepted their incident response plan. They're 3 steps behind us.",
            "Moving funds to Monero for better privacy. XMR wallet setup instructions in the encrypted channel.",
        ],
    },
    "GhostNode": {
        "msgs": [
            "I've compromised the target's VPN gateway. Credentials dumped to the shared drive.",
            "Running Mimikatz on the DC now. Domain admin in 3... 2... 1... got it.",
            "Their SIEM is barely configured. Alert rules are a joke.",
            "Cleaned up the event logs. Windows Security, System, and PowerShell history wiped.",
            "Lateral movement to the finance server complete. Found the database backups.",
            "The target's email server has 14TB of data. Exfiltrating at 50mbps, ETA 3 days.",
            "They hired a new CISO last month. She might actually be competent. We need to accelerate.",
            "Installed backdoor in their update mechanism. Persistent and survives reimaging.",
            "Keylogger data from the CFO's machine is interesting. I'll upload the highlights.",
            "Need more infrastructure. Current botnet has 2,400 nodes but we need 10k for the DDoS.",
            "Their backup strategy is solid — air-gapped tapes. Can't encrypt what we can't reach.",
            "The insider (employee #4471) wants $50,000 upfront. Worth it for the access.",
        ],
    },
    "NullPointer": {
        "msgs": [
            "Source code review complete. Found 3 RCE vulnerabilities in their API.",
            "Compiled the exploit for ARM64. Works on their IoT devices too.",
            "git commit -m 'fixed totally legitimate security improvement'\nI love hiding in plain sight.",
            "The obfuscation layer adds 200ms latency. Acceptable tradeoff for evasion.",
            "Database schema mapped. 47 tables, 12 million customer records. PII goldmine.",
            "Their API rate limiting is broken. I can dump 100k records per minute.",
            "Built a custom implant in Rust. File size: 47KB. Detection rate: 0/67 on VT.",
            "The SSL certificate for the fake domain is ready. Let's Encrypt, ironically.",
            "Decompiled their mobile app. Hardcoded API keys everywhere. Amateur hour.",
            "Fuzzing their payment gateway now. Already found 2 integer overflows.",
            "The WAF blocks basic payloads but my polymorphic encoder gets through every time.",
            "Wrote a PowerShell cradle that bypasses AMSI. Sharing in the tools channel.",
        ],
    },
    "Spectre_Admin": {
        "msgs": [
            "Weekly status update:\n- 3 new targets acquired\n- 2 ransomware payments received ($340k total)\n- 1 infrastructure node burned, replaced",
            "OpSec reminder: NO real names. NO personal devices. NO clearnet access without VPN+Tor.",
            "New member vetting: provide 2 references from trusted groups. 30-day probation period.",
            "Payment distribution:\n- CyberVault: 0.8 BTC\n- GhostNode: 0.6 BTC\n- NullPointer: 0.5 BTC\n- PhantomX: 0.4 BTC",
            "We've been mentioned on a threat intel blog. Laying low for 2 weeks. No new operations.",
            "Emergency: one of our proxy servers was seized. Assume it's burned. Rotate everything.",
            "Recruiting for a social engineering specialist. Know anyone?",
            "Annual revenue projection: $2.1M. Not bad for a decentralized crew.",
            "I've reviewed everyone's operational security. GhostNode — stop reusing usernames across platforms.",
            "New rule: all communications must use ephemeral messages. 24-hour auto-delete.",
            "The law enforcement takedown of Hive was sloppy. We won't make the same mistakes.",
            "Good work this quarter, team. Bonuses distributed to the usual wallets.",
        ],
    },
    "PhantomX": {
        "msgs": [
            "Social engineering the IT helpdesk now. They reset passwords over the phone with just an employee ID.",
            "Created 15 LinkedIn profiles for the spear-phishing campaign. All look legit.",
            "The CEO's personal email password is 'Summer2025!'. People never learn.",
            "Vishing call to the bank went perfectly. They confirmed the wire transfer details.",
            "I've mapped the target org chart. 347 employees. Key targets highlighted.",
            "The fake invoice got approved. $87,000 incoming to our shell company.",
            "Deepfake audio of the CFO is 94% match. Good enough for a phone call.",
            "USB drops at the target's parking lot: 5 of 20 were plugged in. Not great, not terrible.",
            "Their security awareness training is quarterly. Next one is in April. Hit them before that.",
            "Built a convincing clone of their SSO portal. DNS poisoning ready to redirect.",
            "The pretexting worked. Got physical access to the server room for 20 minutes.",
            "Credential stuffing against their VPN: 12 valid accounts found from previous breaches.",
        ],
    },
    "SilentWatcher": {
        "msgs": [
            "Monitoring their SOC Slack channels. They suspect nothing.",
            "Traffic analysis shows they communicate with their incident response firm every Tuesday at 10am.",
            "Passive recon complete. 47 subdomains, 12 exposed services, 3 with known vulns.",
            "Their CTO just posted vacation photos from Bali. Perfect time to strike.",
            "Network diagram reconstructed from SNMP data. Sharing in the intel channel.",
            "I've been inside their network for 67 days. Longest dwell time yet.",
            "Wireshark capture from their internal network: 2.3GB. Analyzing now.",
            "They just deployed CrowdStrike. We need to update our evasion techniques.",
            "The night shift security guard leaves the side door propped open at 11:30pm. Every. Single. Night.",
            "Their disaster recovery site is in Phoenix. Same weak configs as primary.",
            "Email headers reveal they use Mimecast. Known bypass available.",
            "Board meeting notes intercepted. They're discussing the security budget. Ironic timing.",
        ],
    },
}

CSV_PERSONAS = {
    "+12125550199": {"name": "Alpha", "msgs": [
        "Package secured at location A. Moving to extraction point.",
        "Negative on the rendezvous. Too much heat at the intersection.",
        "Confirmed visual on target. Black SUV, plate JKL-4429.",
        "Radio check. All units report status.",
        "Moving to secondary position. ETA 15 minutes.",
        "Contact lost with Bravo team. Last known position: 40.7589° N, 73.9851° W",
        "Requesting backup at the warehouse district.",
        "All clear. Proceeding with phase two.",
        "Intercepted communication mentioning $250,000 transfer.",
        "Target is mobile. Heading northbound on highway 401.",
        "Documents recovered from the safe house. Photographing now.",
        "Need a forensic team at 1847 Industrial Boulevard ASAP.",
        "Wire transfer traced to account ending in 4471. Swiss bank.",
        "Suspect vehicle abandoned at the marina. Running plates now.",
        "Debrief at 0600. Everyone attends. No exceptions.",
    ]},
    "+14165558822": {"name": "Bravo", "msgs": [
        "Copy Alpha. In position at the north entrance.",
        "I see two unknowns entering the building. Armed.",
        "License plate check: registered to a shell company in Delaware.",
        "Following at a distance. Target unaware.",
        "Found a burner phone in the dumpster. Bagging for evidence.",
        "Surveillance camera footage secured. 72 hours of recordings.",
        "The informant says the deal goes down at midnight.",
        "Signal lost in the underground parking. Switching to backup freq.",
        "Tailing suspect to 55 Queen Street West. He's meeting someone.",
        "Photographs uploaded to the secure server. Case file TL-2025-0847.",
        "Confirmed identity: suspect is Marco Reyes, DOB 03/15/1985.",
        "Financial records show 14 suspicious transactions in the last quarter.",
        "The wiretap picked up a reference to 'the doctor'. Cross-referencing.",
        "Evidence locker updated. Chain of custody maintained.",
        "Requesting warrant for premises at 224 Spadina Avenue.",
    ]},
    "+17185550234": {"name": "Charlie", "msgs": [
        "Technical surveillance installed at the target location.",
        "Phone clone successful. Monitoring all incoming and outgoing.",
        "Decrypted message fragment: '...meet at the usual place at 2200...'",
        "Digital forensics on the laptop complete. 47GB of data recovered.",
        "The encrypted partition used AES-256. Took 3 days to crack.",
        "Found a hidden TrueCrypt volume. Contents being analyzed.",
        "Email dump from the suspect's protonmail: 1,247 messages over 8 months.",
        "Malware analysis: custom RAT, communicates over port 8443.",
        "GPS tracker data shows suspect visited the port 14 times this month.",
        "Cell tower triangulation places suspect at the crime scene at 2347 hours.",
        "IMEI tracking: suspect has used 7 different phones in 3 months.",
        "Social media OSINT: suspect's Instagram shows trip to Zurich, Feb 22-28.",
        "Cryptocurrency tracing: $450,000 moved through a mixer, partial trail recovered.",
        "VoIP records show 23 calls to a number in Bogota: +57 1 555 0199.",
        "Full forensic report uploaded. 234 pages. Summary in the first 10.",
    ]},
    "+16475550891": {"name": "Delta", "msgs": [
        "Undercover position maintained. No suspicion from targets.",
        "They're planning something big for next month. Details unclear.",
        "Made contact with the mid-level distributor. Building trust.",
        "The organization has at least 3 layers. I've only accessed the outer one.",
        "Recording from tonight's meeting uploaded. 47 minutes.",
        "They use code words: 'groceries' means product, 'cooking' means processing.",
        "My cover identity is holding. They ran a background check and it passed.",
        "Need extraction plan ready. Things could go sideways fast.",
        "The boss, they call him 'El Arquitecto', I haven't met him yet.",
        "Financial handoff observed: briefcase exchange at Dundas Square, approx $80,000.",
        "They're recruiting from local boxing gyms. 4 new members this month.",
        "Internal conflict brewing. Santos and Danny had a shouting match about money.",
        "The product comes in through the port, disguised as medical supplies.",
        "Weekly meeting is Thursdays at the restaurant on College Street. Back room.",
        "I need to lay low for a few days. They're doing loyalty tests.",
    ]},
    "+19055550342": {"name": "Echo", "msgs": [
        "Analyst report ready. Pattern analysis shows escalation over the past 6 weeks.",
        "Cross-referencing with INTERPOL database. 3 matches found.",
        "Financial intelligence: money flow mapped across 12 jurisdictions.",
        "Link analysis complete. Network diagram attached to case file.",
        "Phone records subpoena returned. 4,721 call records over 6 months.",
        "The organization's communication patterns change every 2 weeks. Adaptive.",
        "Open source intelligence: suspect's wife posted a photo at the Cayman resort.",
        "Travel records: suspect flew Toronto → Panama → Zurich → Toronto in 10 days.",
        "Bank Secrecy Act filing flagged $287,000 in structured deposits.",
        "Predictive analysis suggests next major transaction window: March 18-22.",
        "Updated threat assessment: HIGH. Organization is well-funded and expanding.",
        "Witness protection request filed for informant CI-2247.",
        "Court order approved for real-time cell site location tracking.",
        "The organization has ties to groups in Colombia, Netherlands, and UAE.",
        "Briefing document prepared for the task force meeting on Monday.",
    ]},
}

# ── Generators ────────────────────────────────────────────────────────

def _gen_whatsapp(out_path: Path, msg_count: int = 800):
    """Generate a WhatsApp-style .txt export spanning ~4 months."""
    lines = []

    # System header
    lines.append("[10/1/25, 09:00:00 AM] Messages and calls are end-to-end encrypted. No one outside of this chat, not even WhatsApp, can read or listen to them.")
    lines.append('[10/1/25, 09:00:00 AM] Marco Reyes created group "Inner Circle - DO NOT ADD"')

    personas = list(WHATSAPP_PERSONAS.keys())
    start = datetime(2025, 10, 1, 9, 0, 0)
    cursor = start

    generated = 0
    while generated < msg_count:
        # Simulate realistic cadence
        # 40% chance of burst (1-3 min gap), 30% moderate (10-60 min), 20% hours, 10% days
        r = random.random()
        if r < 0.40:
            gap = timedelta(seconds=random.randint(30, 180))
        elif r < 0.70:
            gap = timedelta(minutes=random.randint(10, 60))
        elif r < 0.90:
            gap = timedelta(hours=random.randint(1, 8))
        else:
            gap = timedelta(days=random.randint(1, 5))

        cursor += gap

        # System events occasionally
        if random.random() < 0.03:
            events = [
                f"{random.choice(personas[:3])} changed the subject to \"Inner Circle - {random.choice(['URGENT', 'SECURE', 'EYES ONLY', 'CODE RED'])}\"",
                f"{random.choice(personas[:3])} added {'+1 ({}) 555-{:04d}'.format(random.randint(200,999), random.randint(1000,9999))}",
                f"{random.choice(personas[:3])} removed {random.choice(personas[3:])}",
            ]
            ts = f"{cursor.month}/{cursor.day}/{cursor.strftime('%y')}, {cursor.strftime('%I').lstrip('0')}:{cursor.strftime('%M:%S')} {cursor.strftime('%p')}"
            lines.append(f"[{ts}] {random.choice(events)}")
            continue

        # Pick sender — weighted: organizer and logistics talk more
        weights = [5, 4, 3, 2, 2, 2, 1]
        sender = random.choices(personas, weights=weights[:len(personas)], k=1)[0]
        persona = WHATSAPP_PERSONAS[sender]

        # Pick message
        msg = random.choice(persona["msgs"])

        # Occasionally add extra context or multi-line
        if random.random() < 0.15:
            extras = [
                "\nThis is urgent.",
                "\nUpdate me ASAP.",
                "\nDon't share this with anyone.",
                f"\nCall me at +1 ({random.randint(200,999)}) 555-{random.randint(1000,9999):04d}",
                f"\nSending ${random.randint(1,50) * 1000:,} tonight.",
                "\nI'll follow up tomorrow morning.",
            ]
            msg += random.choice(extras)

        ts = f"{cursor.month}/{cursor.day}/{cursor.strftime('%y')}, {cursor.strftime('%I').lstrip('0')}:{cursor.strftime('%M:%S')} {cursor.strftime('%p')}"
        lines.append(f"[{ts}] {sender}: {msg}")
        generated += 1

    # Final system event
    ts = f"{cursor.month}/{cursor.day}/{cursor.strftime('%y')}, {cursor.strftime('%I').lstrip('0')}:{cursor.strftime('%M:%S')} {cursor.strftime('%p')}"
    lines.append(f"[{ts}] Marco Reyes changed the subject to \"[ARCHIVED]\"")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  WhatsApp: {out_path} ({generated} messages, {len(lines)} lines)")


def _gen_telegram(out_path: Path, msg_count: int = 600):
    """Generate a Telegram-style JSON export spanning ~6 months."""
    personas = list(TELEGRAM_PERSONAS.keys())
    start = datetime(2025, 6, 1, 0, 0, 0)
    cursor = start
    msg_id = 1000

    messages = []
    msg_ids_by_sender: dict[str, list[int]] = {}

    # Service message: group created
    messages.append({
        "id": msg_id,
        "type": "service",
        "date": cursor.strftime("%Y-%m-%dT%H:%M:%S"),
        "date_unixtime": str(int(cursor.timestamp())),
        "actor": "Spectre_Admin",
        "actor_id": "user_000000001",
        "action": "create_group",
        "title": "Project Spectre // Authorized Personnel Only"
    })
    msg_id += 1

    generated = 0
    while generated < msg_count:
        r = random.random()
        if r < 0.35:
            gap = timedelta(seconds=random.randint(10, 120))
        elif r < 0.65:
            gap = timedelta(minutes=random.randint(5, 90))
        elif r < 0.85:
            gap = timedelta(hours=random.randint(2, 12))
        else:
            gap = timedelta(days=random.randint(1, 7))
        cursor += gap

        # Service events occasionally
        if random.random() < 0.02:
            messages.append({
                "id": msg_id,
                "type": "service",
                "date": cursor.strftime("%Y-%m-%dT%H:%M:%S"),
                "date_unixtime": str(int(cursor.timestamp())),
                "actor": random.choice(personas),
                "actor_id": f"user_{random.randint(100000, 999999):09d}",
                "action": random.choice(["pin_message", "edit_group_title", "edit_group_photo"]),
            })
            msg_id += 1
            continue

        sender = random.choice(personas)
        persona = TELEGRAM_PERSONAS[sender]
        text = random.choice(persona["msgs"])
        user_id = f"user_{abs(hash(sender)) % 999999999:09d}"

        # Reply to previous message sometimes
        reply_to = None
        if random.random() < 0.3 and generated > 5:
            # Reply to someone else's message
            other_senders = [s for s in msg_ids_by_sender if s != sender]
            if other_senders:
                reply_sender = random.choice(other_senders)
                if msg_ids_by_sender[reply_sender]:
                    reply_to = random.choice(msg_ids_by_sender[reply_sender])

        # Build text_entities
        entities = [{"type": "plain", "text": text}]

        # Sometimes add mixed entity types (like Telegram does)
        if "http" in text or ".onion" in text:
            entities.append({"type": "link", "text": text.split()[-1]})

        msg_obj = {
            "id": msg_id,
            "type": "message",
            "date": cursor.strftime("%Y-%m-%dT%H:%M:%S"),
            "date_unixtime": str(int(cursor.timestamp())),
            "from": sender,
            "from_id": user_id,
            "text": text,
            "text_entities": entities,
        }

        if reply_to:
            msg_obj["reply_to_message_id"] = reply_to

        # Occasionally add forwarded_from
        if random.random() < 0.05:
            msg_obj["forwarded_from"] = random.choice([s for s in personas if s != sender])

        # Occasionally add file attachment
        if random.random() < 0.08:
            attachments = [
                ("network_diagram.png", "image/png", 2457600),
                ("credentials_dump.txt", "text/plain", 145200),
                ("exploit_v3.7.zip", "application/zip", 8847200),
                ("recording_2025.opus", "audio/opus", 4512000),
                ("screenshot_soc.jpg", "image/jpeg", 1847000),
                ("database_backup.sql.gz", "application/gzip", 67584000),
            ]
            fname, mime, size = random.choice(attachments)
            msg_obj["file"] = fname
            msg_obj["mime_type"] = mime
            msg_obj["size_bytes"] = size

        # Occasionally null out from (deleted account simulation)
        if random.random() < 0.02:
            msg_obj["from"] = None
            msg_obj["from_id"] = None

        messages.append(msg_obj)
        msg_ids_by_sender.setdefault(sender, []).append(msg_id)
        msg_id += 1
        generated += 1

    data = {
        "name": "Project Spectre // Authorized Personnel Only",
        "type": "private_supergroup",
        "id": -1001234567890,
        "messages": messages,
    }

    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Telegram: {out_path} ({generated} messages)")


def _gen_csv(out_path: Path, msg_count: int = 1000):
    """Generate a CSV surveillance log spanning ~5 months."""
    personas = list(CSV_PERSONAS.keys())
    start = datetime(2025, 9, 1, 6, 0, 0)
    cursor = start

    rows = []
    generated = 0

    while generated < msg_count:
        r = random.random()
        if r < 0.35:
            gap = timedelta(seconds=random.randint(15, 120))
        elif r < 0.65:
            gap = timedelta(minutes=random.randint(3, 45))
        elif r < 0.85:
            gap = timedelta(hours=random.randint(1, 6))
        else:
            gap = timedelta(days=random.randint(1, 4))
        cursor += gap

        sender = random.choice(personas)
        persona = CSV_PERSONAS[sender]
        body = random.choice(persona["msgs"])

        # Pick a recipient (someone other than sender)
        recipient = random.choice([p for p in personas if p != sender])

        # Vary timestamp formats slightly (but keep them parseable)
        ts = cursor.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Status
        status = random.choices(
            ["Delivered", "Read", "Sent", "Failed"],
            weights=[50, 35, 10, 5],
            k=1
        )[0]

        # Attachment occasionally
        attachment = ""
        if random.random() < 0.1:
            attachments = [
                "/evidence/photos/IMG_" + str(random.randint(1000, 9999)) + ".jpg",
                "/evidence/audio/REC_" + cursor.strftime("%Y%m%d") + ".m4a",
                "/evidence/docs/scan_" + str(random.randint(100, 999)) + ".pdf",
                "/evidence/video/surveil_" + str(random.randint(10, 99)) + ".mp4",
            ]
            attachment = random.choice(attachments)

        rows.append({
            "Timestamp (UTC)": ts,
            "Sender ID": sender,
            "Recipient ID": recipient,
            "Message Body": body,
            "Attachment Path": attachment,
            "Status": status,
            "Case Reference": f"TL-2025-{random.randint(800,899):04d}",
        })
        generated += 1

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"  CSV: {out_path} ({generated} messages)")


if __name__ == "__main__":
    print("Generating realistic test data...")
    _gen_whatsapp(OUT_DIR / "operation_inner_circle.txt", msg_count=800)
    _gen_telegram(OUT_DIR / "project_spectre.json", msg_count=600)
    _gen_csv(OUT_DIR / "surveillance_log.csv", msg_count=1000)
    print(f"\nAll files written to: {OUT_DIR}")
    print("Ready for testing.")
