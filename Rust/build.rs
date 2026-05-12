use std::process::Command;

fn main() {
    println!("cargo::rerun-if-changed=build_static_tables.py");
    println!("cargo::rerun-if-changed=lib.src.rs");
    println!("cargo::rerun-if-changed=../sourceTables/Hebrew.tsv");
    println!("cargo::rerun-if-changed=../sourceTables/Greek.tsv");

    let output = Command::new("python3")
        .arg("build_static_tables.py")
        .output()
        .expect("Failed to execute build_static_tables.py");

    if !output.stdout.contains(&b'$') {
        panic!("Python build script failed!!!\nStdout: {}\nStderr: {}", 
            String::from_utf8_lossy(&output.stdout),
            String::from_utf8_lossy(&output.stderr));
    }
}
