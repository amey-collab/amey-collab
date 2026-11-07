name: 🐍 Generate Contribution Snake

on:
  schedule:
    - cron: "0 */6 * * *"     # every 6 hours
  workflow_dispatch:           # manual "Run workflow" button
  push:
    branches:
      - main

permissions:
  contents: write

concurrency:
  group: snake-${{ github.ref }}
  cancel-in-progress: true

jobs:
  generate:
    name: Build & publish snake animations
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: 🎨 Generate snake animations (multi-theme)
        uses: Platane/snk@v3
        with:
          github_user_name: ${{ github.repository_owner }}
          outputs: |
            dist/snake-light.svg?color_snake=#7209b7&color_dots=#ebedf0,#a5f3fc,#22d3ee,#c026d3,#7209b7
            dist/snake-dark.svg?palette=github-dark&color_snake=#00f5ff&color_dots=#161b22,#3a0ca3,#7209b7,#b5179e,#ff00ff
            dist/snake-neon.svg?palette=github-dark&color_snake=#00f5d4&color_dots=#0d1117,#00bbf9,#00f5d4,#9b5de5,#f15bb5
            dist/snake-ocean.svg?color_snake=#0ea5e9&color_dots=#e0f2fe,#7dd3fc,#38bdf8,#0284c7,#075985
            dist/snake-classic.svg
            dist/snake-classic-dark.svg?palette=github-dark
            dist/snake.gif?color_snake=#00f5ff&color_dots=#161b22,#3a0ca3,#7209b7,#b5179e,#ff00ff

      - name: 🔍 Verify generated files
        run: ls -lh dist/

      - name: 🚀 Publish to output branch
        uses: crazy-max/ghaction-github-pages@v4
        with:
          target_branch: output
          build_dir: dist
          commit_message: "🐍 Update contribution snake [skip ci]"
          keep_history: false
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
