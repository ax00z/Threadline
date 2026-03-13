import pytest
from threadline.ner import extract_entities, extract_from_messages, spacy_available

needs_spacy = pytest.mark.skipif(not spacy_available(), reason="spacy not installed")


def test_phone_extraction():
    ents = extract_entities("call me at +1-555-123-4567 ok?")
    phones = [e for e in ents if e.label == "PHONE"]
    assert len(phones) >= 1
    assert "555" in phones[0].text


def test_email_extraction():
    ents = extract_entities("send it to bob@example.com")
    emails = [e for e in ents if e.label == "EMAIL"]
    assert len(emails) == 1
    assert emails[0].text == "bob@example.com"


def test_url_extraction():
    ents = extract_entities("check https://shady-site.com/page?q=1 out")
    urls = [e for e in ents if e.label == "URL"]
    assert len(urls) == 1
    assert "shady-site.com" in urls[0].text


def test_money_extraction():
    ents = extract_entities("he paid $1,200.50 for it")
    money = [e for e in ents if e.label == "MONEY"]
    assert len(money) == 1
    assert "1,200" in money[0].text


def test_crypto_wallet():
    eth = "0x" + "a1b2c3d4" * 5
    ents = extract_entities(f"send to {eth}")
    wallets = [e for e in ents if e.label == "CRYPTO_WALLET"]
    assert len(wallets) == 1


def test_coordinates():
    ents = extract_entities("meet at 40.7128, -74.0060")
    coords = [e for e in ents if e.label == "COORDINATES"]
    assert len(coords) == 1


def test_no_overlap():
    text = "email bob@example.com about it"
    ents = extract_entities(text)
    spans = [(e.start, e.end) for e in ents]
    for i, (s1, e1) in enumerate(spans):
        for s2, e2 in spans[i + 1:]:
            assert s1 >= e2 or s2 >= e1, f"overlap: ({s1},{e1}) vs ({s2},{e2})"


def test_short_phone_filtered():
    ents = extract_entities("dial 123")
    phones = [e for e in ents if e.label == "PHONE"]
    assert len(phones) == 0


def test_extract_from_messages_shape():
    msgs = [
        {"body": "call +1-555-999-0000", "sender": "Marcus", "timestamp": "2025-01-01T10:00:00"},
        {"body": "ok got it", "sender": "Kofi", "timestamp": "2025-01-01T10:01:00"},
    ]
    result = extract_from_messages(msgs)
    assert "entities" in result
    assert "unique_entities" in result
    assert "label_counts" in result
    assert "sender_entities" in result
    assert "total_found" in result
    assert result["total_found"] >= 1


def test_extract_from_messages_dedup():
    msgs = [
        {"body": "call +1-555-999-0000", "sender": "A", "timestamp": ""},
        {"body": "also +1-555-999-0000", "sender": "B", "timestamp": ""},
    ]
    result = extract_from_messages(msgs)
    phones = [e for e in result["unique_entities"] if e["label"] == "PHONE"]
    assert len(phones) >= 1, "should find at least one phone"
    matching = [p for p in phones if "555-999-0000" in p["text"]]
    assert len(matching) == 1, "same number should be deduped into one entry"
    assert matching[0]["count"] == 2
    assert len(matching[0]["senders"]) == 2


@needs_spacy
def test_spacy_person():
    ents = extract_entities("I talked to John Smith about the deal")
    persons = [e for e in ents if e.label == "PERSON"]
    assert len(persons) >= 1
    assert any("John" in p.text for p in persons)


@needs_spacy
def test_spacy_org():
    ents = extract_entities("he works at Goldman Sachs now")
    orgs = [e for e in ents if e.label == "ORG"]
    assert len(orgs) >= 1


@needs_spacy
def test_spacy_location():
    ents = extract_entities("they flew to Berlin last week")
    locs = [e for e in ents if e.label == "LOCATION"]
    assert len(locs) >= 1
    assert any("Berlin" in l.text for l in locs)


@needs_spacy
def test_regex_wins_over_spacy():
    text = "email john@test.com from New York"
    ents = extract_entities(text)
    emails = [e for e in ents if e.label == "EMAIL"]
    assert len(emails) == 1
    assert emails[0].text == "john@test.com"
