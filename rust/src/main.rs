use sha2::{Digest, Sha256};
use std::io::{self, BufRead};

/// fields that go into the canonical hash, alphabetical order
const HASH_FIELDS: &[&str] = &[
    "body",
    "line_number",
    "sender",
    "source_format",
    "timestamp",
];

fn canonical(msg: &serde_json::Value) -> String {
    let mut parts = Vec::with_capacity(HASH_FIELDS.len());
    for &key in HASH_FIELDS {
        if let Some(val) = msg.get(key) {
            // serde_json compact form already uses no spaces
            parts.push(format!("\"{}\":{}", key, compact_value(val)));
        }
    }
    format!("{{{}}}", parts.join(","))
}

/// match python's json.dumps separators=(",",":") output
fn compact_value(v: &serde_json::Value) -> String {
    match v {
        serde_json::Value::String(s) => serde_json::to_string(s).unwrap(),
        serde_json::Value::Number(n) => n.to_string(),
        serde_json::Value::Bool(b) => b.to_string(),
        serde_json::Value::Null => "null".to_string(),
        _ => serde_json::to_string(v).unwrap(),
    }
}

fn sha256_hex(data: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data.as_bytes());
    format!("{:x}", hasher.finalize())
}

const GENESIS: &str = "0000000000000000000000000000000000000000000000000000000000000000";

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let reader: Box<dyn BufRead> = if args.len() > 1 && args[1] != "-" {
        let file = std::fs::File::open(&args[1]).unwrap_or_else(|e| {
            eprintln!("error: cannot open '{}': {}", args[1], e);
            std::process::exit(1);
        });
        Box::new(io::BufReader::new(file))
    } else {
        Box::new(io::BufReader::new(io::stdin()))
    };

    let mut prev = GENESIS.to_string();
    let mut count = 0;

    for (i, line) in reader.lines().enumerate() {
        let line = line.unwrap_or_else(|e| {
            eprintln!("error reading line {}: {}", i + 1, e);
            std::process::exit(1);
        });
        let line = line.trim();
        if line.is_empty() {
            continue;
        }

        let msg: serde_json::Value = serde_json::from_str(line).unwrap_or_else(|e| {
            eprintln!("error: invalid JSON on line {}: {}", i + 1, e);
            std::process::exit(1);
        });

        let stored_hash = msg
            .get("chain_hash")
            .and_then(|v| v.as_str())
            .unwrap_or_else(|| {
                eprintln!("error: missing chain_hash on message {}", i);
                std::process::exit(1);
            });

        let stored_prev = msg
            .get("previous_hash")
            .and_then(|v| v.as_str())
            .unwrap_or_else(|| {
                eprintln!("error: missing previous_hash on message {}", i);
                std::process::exit(1);
            });

        // check the previous_hash pointer
        if stored_prev != prev {
            eprintln!(
                "FAIL: chain broken at message {} — previous_hash mismatch",
                i
            );
            std::process::exit(2);
        }

        let content_hash = sha256_hex(&canonical(&msg));
        let expected = sha256_hex(&format!("{}{}", content_hash, prev));

        if expected != stored_hash {
            eprintln!(
                "FAIL: chain broken at message {} — hash mismatch (expected {}, got {})",
                i,
                &expected[..12],
                &stored_hash[..12]
            );
            std::process::exit(2);
        }

        prev = stored_hash.to_string();
        count += 1;
    }

    println!("OK — {} messages verified, chain intact", count);
}
