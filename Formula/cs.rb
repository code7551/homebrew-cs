class Cs < Formula
  desc "Searchable picker that resumes Claude Code chats in their project folder"
  homepage "https://github.com/code7551/homebrew-cs"
  url "https://github.com/code7551/homebrew-cs/archive/refs/tags/v1.1.0.tar.gz"
  sha256 "53988578d03a5a1d1e5af03345b7f6e9ef494c651941be3977ca09d3b260b163"

  def install
    bin.install "claude-sessions"
  end

  def caveats
    <<~'EOS'
      Add cs to your ~/.zshrc (run this once):
        printf '\n%s\n' '(( $+commands[claude-sessions] )) && eval "$(claude-sessions init zsh)"' >> ~/.zshrc

      Then run `source ~/.zshrc` (or open a new terminal tab) and run `cs`.
    EOS
  end

  test do
    assert_match "claude-sessions #{version}", shell_output("#{bin}/claude-sessions --version")
    assert_match "function cs", shell_output("#{bin}/claude-sessions init zsh")
  end
end
