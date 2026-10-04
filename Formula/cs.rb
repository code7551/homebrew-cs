class Cs < Formula
  desc "Searchable picker that resumes Claude Code chats in their project folder"
  homepage "https://github.com/code7551/homebrew-cs"
  url "https://github.com/code7551/homebrew-cs/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "33fcc9ede1fe97fd31d722c167196fc1d32b9a1792ebdc60368bd8c4df88669c"

  def install
    bin.install "claude-sessions"
  end

  def caveats
    <<~EOS
      Add this line to ~/.zshrc, then open a new terminal:
        (( $+commands[claude-sessions] )) && eval "$(claude-sessions init zsh)"

      Then run `cs` to search your Claude Code chats and resume one.
    EOS
  end

  test do
    assert_match "claude-sessions #{version}", shell_output("#{bin}/claude-sessions --version")
    assert_match "function cs", shell_output("#{bin}/claude-sessions init zsh")
  end
end
