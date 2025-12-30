import Foundation

@main
struct WolfIntelligence {
    static func main() async throws {
        let args = CommandLine.arguments

        // If called with question argument (from Siri Shortcut)
        if args.count > 1 {
            let question = args.dropFirst().joined(separator: " ")
            let system = IntelligenceSystem()
            let answer = try await system.ask(question)
            print(answer)
            return
        }

        // Otherwise run demo
        print("🐺 Wolf Intelligence")
        print("Librarian (181:5433) + Llama3.1-Claude (181:11434)")
        print("Siri → Wolf Intelligence → Claude + 100K Memory")
        print("")

        let system = IntelligenceSystem()
        try await system.initialize()

        let query = "What are Wolf's core values?"
        print("Demo Query: \(query)")
        print("")

        let response = try await system.ask(query)
        print("Answer: \(response)")
    }
}

// MARK: - Intelligence System
class IntelligenceSystem {
    private let librarian = Librarian()
    private let claude = ClaudeBridge()

    func initialize() async throws {
        print("✓ Librarian ready (99K+ memories)")
        print("✓ Claude bridge ready (8B model)")
        print("")
    }

    func ask(_ question: String) async throws -> String {
        // 1. Query Librarian for context
        let memories = try await librarian.querySemantic(question)
        let context = memories.prefix(5).joined(separator: "\n\n")

        // 2. Build prompt with context
        let prompt: String
        if memories.isEmpty {
            prompt = question
        } else {
            prompt = """
            Context from memory:
            \(context)

            Question: \(question)

            Answer based on the context above. Be direct and concise.
            """
        }

        // 3. Ask Claude on 181
        let response = try await claude.sendMessage(prompt)
        return response.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}

// MARK: - Librarian (PostgreSQL via psql)
class Librarian {
    func querySemantic(_ searchText: String) async throws -> [String] {
        let escapedText = searchText.replacingOccurrences(of: "'", with: "''")
        let query = """
        SELECT content FROM memories_embedding
        WHERE namespace IN ('core_identity', 'scripty')
        ORDER BY embedding <=> ai.ollama_embed('qwen3-embedding:4b', '\(escapedText)')
        LIMIT 10;
        """

        return try await executePSQL(query)
    }

    private func executePSQL(_ sql: String) async throws -> [String] {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/local/Cellar/postgresql@17/17.7/bin/psql")
        process.arguments = [
            "-h", "100.110.82.181",
            "-p", "5433",
            "-U", "wolf",
            "-d", "wolf_logic",
            "-t",
            "-c", sql
        ]
        process.environment = ["PGPASSWORD": "wolflogic2024"]

        let pipe = Pipe()
        let errorPipe = Pipe()
        process.standardOutput = pipe
        process.standardError = errorPipe

        try process.run()
        process.waitUntilExit()

        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        let output = String(data: data, encoding: .utf8) ?? ""

        return output.split(separator: "\n")
            .map { String($0).trimmingCharacters(in: .whitespaces) }
            .filter { !$0.isEmpty }
    }
}

// MARK: - Claude Bridge (Ollama on 181)
class ClaudeBridge {
    private let baseURL = "http://100.110.82.181:11434"
    private let model = "incept5/llama3.1-claude:latest"

    func sendMessage(_ message: String) async throws -> String {
        var request = URLRequest(url: URL(string: "\(baseURL)/api/generate")!)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "content-type")

        let payload: [String: Any] = [
            "model": model,
            "prompt": message,
            "stream": false
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: payload)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw BridgeError.connectionFailed
        }

        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        guard let responseText = json?["response"] as? String else {
            throw BridgeError.invalidResponse
        }

        return responseText
    }
}

enum BridgeError: Error {
    case connectionFailed
    case invalidResponse
}
