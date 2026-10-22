// Zest.app front end (ADR-011; US-41). Built by build_dmg.sh with `swiftc -target arm64-apple-macos14.0`.
// A normal Dock app with no window: opening it starts zest-server.sh (the Python launcher), clicking the
// Dock icon reopens Zest in the browser, and Quit (Cmd-Q, the Dock menu, logout or shutdown) sends SIGTERM
// so the launcher stops the API server and any Ollama it started. If the server exits, the app quits too.
import AppKit

final class ZestApp: NSObject, NSApplicationDelegate {
    private var server: Process?
    // The data folder name comes from Info.plist (ZestRuntimeFolder), so 1.0 and 2.0 never share one (ADR-012)
    private let runtime = ProcessInfo.processInfo.environment["ZEST_RUNTIME_DIR"].map { URL(fileURLWithPath: $0) }
        ?? FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Application Support")
            .appendingPathComponent(Bundle.main.object(forInfoDictionaryKey: "ZestRuntimeFolder") as? String ?? "Zest")

    private var sigterm: DispatchSourceSignal?

    func applicationDidFinishLaunching(_ note: Notification) {
        NSApp.mainMenu = Self.menu()
        signal(SIGTERM, SIG_IGN)  // a SIGTERM to the app is a normal Quit, so the server is stopped too
        sigterm = DispatchSource.makeSignalSource(signal: SIGTERM, queue: .main)
        sigterm?.setEventHandler { [weak self] in self?.onMain(#selector(ZestApp.quit)) }
        sigterm?.resume()
        let script = Bundle.main.resourceURL!.appendingPathComponent("zest-server.sh")
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/bash")
        process.arguments = [script.path]
        process.terminationHandler = { [weak self] _ in self?.onMain(#selector(ZestApp.quit)) }
        do {
            try process.run()
            server = process
        } catch {
            let alert = NSAlert()
            alert.messageText = "Zest could not start"
            alert.informativeText = error.localizedDescription
            alert.runModal()
            NSApp.terminate(nil)
        }
    }

    // Dock icon clicked (or the app opened again) while running: show Zest in the browser.
    func applicationShouldHandleReopen(_ app: NSApplication, hasVisibleWindows: Bool) -> Bool {
        if let port = launcherPort() {
            NSWorkspace.shared.open(URL(string: "http://127.0.0.1:\(port)/launcher/")!)  // forwards to Zest when ready
        }
        return false
    }

    func applicationShouldTerminate(_ app: NSApplication) -> NSApplication.TerminateReply {
        guard let process = server, process.isRunning else { return .terminateNow }
        process.terminationHandler = nil
        process.terminate()  // SIGTERM: the launcher shuts down uvicorn and its private Ollama
        DispatchQueue.global().async {
            let deadline = Date().addingTimeInterval(15)
            while process.isRunning && Date() < deadline { usleep(200_000) }
            if process.isRunning { kill(process.processIdentifier, SIGKILL) }
            self.onMain(#selector(ZestApp.finishQuit))
        }
        return .terminateLater
    }

    func applicationDockMenu(_ sender: NSApplication) -> NSMenu? {
        let menu = NSMenu()
        menu.addItem(withTitle: "Open Zest in Browser", action: #selector(openZest), keyEquivalent: "").target = self
        return menu
    }

    private func launcherPort() -> Int? {
        guard let data = try? Data(contentsOf: runtime.appendingPathComponent("launcher.json")),
              let info = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return nil }
        return info["port"] as? Int
    }

    private static func menu() -> NSMenu {
        let main = NSMenu()
        let item = NSMenuItem()
        main.addItem(item)
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "Open Zest in Browser", action: #selector(openZest), keyEquivalent: "o").target = NSApp.delegate
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "Quit Zest", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        item.submenu = appMenu
        return main
    }

    // Through the main run loop, not the main dispatch queue: while AppKit waits for the terminate reply it keeps
    // serving run-loop sources, but a main-queue block that started the quit would block the queue (and the reply).
    private func onMain(_ selector: Selector) {
        performSelector(onMainThread: selector, with: nil, waitUntilDone: false,
                        modes: [RunLoop.Mode.common.rawValue, RunLoop.Mode.modalPanel.rawValue])
    }

    @objc func quit() { NSApp.terminate(nil) }

    @objc func finishQuit() { NSApp.reply(toApplicationShouldTerminate: true) }

    @objc func openZest() { _ = applicationShouldHandleReopen(NSApp, hasVisibleWindows: false) }
}

let app = NSApplication.shared
let delegate = ZestApp()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
