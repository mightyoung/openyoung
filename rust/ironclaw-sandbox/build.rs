fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Compile all proto files
    tonic_build::configure()
        .build_server(true)
        .build_client(true)
        .compile(
            &[
                "proto/security.proto",
                "proto/agent_control.proto",
                "proto/evaluator.proto",
            ],
            &["proto/"],
        )?;
    Ok(())
}
