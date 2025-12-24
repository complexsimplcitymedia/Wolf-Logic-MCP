// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "WolfIntelligence",
    platforms: [
        .macOS(.v12)
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "WolfIntelligence",
            dependencies: []
        ),
    ]
)
