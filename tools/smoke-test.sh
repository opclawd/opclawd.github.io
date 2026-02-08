#!/usr/bin/env bash
#
# OpenClaw Smoke Test - Quick pre-flight validation
#
# Curls main pages, validates index.json, counts tests, reports issues.
# Designed to complete in under 5 seconds.
#
# Usage: bash tools/smoke-test.sh
# Run from workspace root: /home/node/.openclaw/workspace/
#

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL="http://clawdbot-web/clawdbot"
PROJECTS_URL="${BASE_URL}/projects"
PUBLIC_DIR="public/clawdbot"
PROJECTS_DIR="${PUBLIC_DIR}/projects"
INDEX_JSON="${PROJECTS_DIR}/index.json"

# Colors
RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
CYAN='\033[96m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# Counters
PASS=0
FAIL=0
WARN=0
TOTAL=0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
ok()   { TOTAL=$((TOTAL+1)); PASS=$((PASS+1));  printf "  ${GREEN}PASS${RESET} %s\n" "$1"; }
fail() { TOTAL=$((TOTAL+1)); FAIL=$((FAIL+1));  printf "  ${RED}FAIL${RESET} %s\n" "$1"; }
warn() { TOTAL=$((TOTAL+1)); WARN=$((WARN+1));  printf "  ${YELLOW}WARN${RESET} %s\n" "$1"; }
info() { printf "  ${DIM}%s${RESET}\n" "$1"; }

check_http() {
    local url="$1"
    local label="$2"
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 --max-time 5 "$url" 2>/dev/null || echo "000")
    if [ "$code" = "200" ]; then
        ok "$label (HTTP $code)"
    else
        fail "$label (HTTP $code)"
    fi
}

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
printf "\n${BOLD}============================================================\n"
printf "  OpenClaw Smoke Test\n"
printf "============================================================${RESET}\n"
printf "  ${DIM}Time:  $(date -u '+%Y-%m-%d %H:%M:%S UTC')${RESET}\n"
printf "  ${DIM}Dir:   $(pwd)${RESET}\n\n"

START_TIME=$(date +%s%N 2>/dev/null || date +%s)

# ---------------------------------------------------------------------------
# 1. Check main pages via HTTP
# ---------------------------------------------------------------------------
printf "${BOLD}[1/4] HTTP Connectivity${RESET}\n"
check_http "${BASE_URL}/"          "Main page /clawdbot/"
check_http "${BASE_URL}/index.html" "Main index.html"
check_http "${PROJECTS_URL}/"       "Projects listing"
check_http "${PROJECTS_URL}/index.json" "index.json endpoint"

# ---------------------------------------------------------------------------
# 2. Validate index.json with jq
# ---------------------------------------------------------------------------
printf "\n${BOLD}[2/4] index.json Validation${RESET}\n"

if [ ! -f "$INDEX_JSON" ]; then
    fail "index.json file not found at $INDEX_JSON"
else
    # Valid JSON?
    if jq empty "$INDEX_JSON" 2>/dev/null; then
        ok "index.json is valid JSON"
    else
        fail "index.json is not valid JSON"
    fi

    # Is array?
    if jq -e 'type == "array"' "$INDEX_JSON" >/dev/null 2>&1; then
        ENTRY_COUNT=$(jq length "$INDEX_JSON")
        ok "index.json has $ENTRY_COUNT entries"
    else
        fail "index.json root is not an array"
        ENTRY_COUNT=0
    fi

    # Count statuses
    if [ "${ENTRY_COUNT:-0}" -gt 0 ]; then
        PASS_COUNT=$(jq '[.[] | select(.status == "PASS")] | length' "$INDEX_JSON" 2>/dev/null || echo 0)
        FAIL_COUNT=$(jq '[.[] | select(.status == "FAIL")] | length' "$INDEX_JSON" 2>/dev/null || echo 0)
        PENDING_COUNT=$(jq '[.[] | select(.status == "PENDING")] | length' "$INDEX_JSON" 2>/dev/null || echo 0)
        info "Statuses: $PASS_COUNT PASS, $FAIL_COUNT FAIL, $PENDING_COUNT PENDING"
    fi

    # Check all file references exist
    BROKEN_REFS=0
    if [ "${ENTRY_COUNT:-0}" -gt 0 ]; then
        while IFS= read -r file_ref; do
            if [ -n "$file_ref" ] && [ ! -f "${PROJECTS_DIR}/${file_ref}" ]; then
                BROKEN_REFS=$((BROKEN_REFS+1))
            fi
        done < <(jq -r '.[].file // empty' "$INDEX_JSON" 2>/dev/null)

        if [ "$BROKEN_REFS" -eq 0 ]; then
            ok "All file references in index.json point to existing files"
        else
            fail "$BROKEN_REFS broken file reference(s) in index.json"
        fi
    fi
fi

# ---------------------------------------------------------------------------
# 3. Count tests and check for missing pages
# ---------------------------------------------------------------------------
printf "\n${BOLD}[3/4] Test Pages Inventory${RESET}\n"

if [ ! -d "$PROJECTS_DIR" ]; then
    fail "Projects directory not found: $PROJECTS_DIR"
else
    DIR_COUNT=0
    MISSING_INDEX=0
    EMPTY_FILES=0
    MISSING_DIRS=""

    for d in "$PROJECTS_DIR"/test-*/; do
        [ -d "$d" ] || continue
        DIR_COUNT=$((DIR_COUNT+1))
        dirname=$(basename "$d")

        if [ ! -f "${d}index.html" ]; then
            MISSING_INDEX=$((MISSING_INDEX+1))
            MISSING_DIRS="${MISSING_DIRS} ${dirname}"
        elif [ ! -s "${d}index.html" ]; then
            EMPTY_FILES=$((EMPTY_FILES+1))
            MISSING_DIRS="${MISSING_DIRS} ${dirname}(empty)"
        fi
    done

    ok "Found $DIR_COUNT test directories"

    if [ "$MISSING_INDEX" -eq 0 ] && [ "$EMPTY_FILES" -eq 0 ]; then
        ok "All test directories have non-empty index.html"
    else
        if [ "$MISSING_INDEX" -gt 0 ]; then
            fail "$MISSING_INDEX test(s) missing index.html"
        fi
        if [ "$EMPTY_FILES" -gt 0 ]; then
            warn "$EMPTY_FILES test(s) have empty index.html"
        fi
        info "Affected:${MISSING_DIRS}"
    fi

    # Check for directories not in index.json
    if [ -f "$INDEX_JSON" ]; then
        UNINDEXED=0
        INDEXED_DIRS=$(jq -r '.[].file // empty' "$INDEX_JSON" 2>/dev/null | sed 's|/.*||' | sort -u)
        for d in "$PROJECTS_DIR"/test-*/; do
            [ -d "$d" ] || continue
            dirname=$(basename "$d")
            if ! echo "$INDEXED_DIRS" | grep -qx "$dirname"; then
                UNINDEXED=$((UNINDEXED+1))
            fi
        done
        if [ "$UNINDEXED" -eq 0 ]; then
            ok "All directories have index.json entries"
        else
            warn "$UNINDEXED directory(ies) not listed in index.json"
        fi
    fi
fi

# ---------------------------------------------------------------------------
# 4. Quick HTTP spot-check on a few test pages
# ---------------------------------------------------------------------------
printf "\n${BOLD}[4/4] HTTP Spot Check (first 3 + last)${RESET}\n"

if [ -d "$PROJECTS_DIR" ]; then
    # Get sorted list of test dirs
    ALL_TESTS=($(ls -d "$PROJECTS_DIR"/test-*/ 2>/dev/null | sort -V))
    NUM_TESTS=${#ALL_TESTS[@]}

    if [ "$NUM_TESTS" -gt 0 ]; then
        # Check first 3
        for i in 0 1 2; do
            if [ $i -lt $NUM_TESTS ]; then
                t=$(basename "${ALL_TESTS[$i]}")
                check_http "${PROJECTS_URL}/${t}/index.html" "${t}/index.html"
            fi
        done

        # Check last one if different from first 3
        LAST_IDX=$((NUM_TESTS - 1))
        if [ $LAST_IDX -gt 2 ]; then
            t=$(basename "${ALL_TESTS[$LAST_IDX]}")
            check_http "${PROJECTS_URL}/${t}/index.html" "${t}/index.html (last)"
        fi
    else
        warn "No test directories found for HTTP checks"
    fi
else
    fail "Cannot perform HTTP spot check - projects dir missing"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
END_TIME=$(date +%s%N 2>/dev/null || date +%s)

# Calculate elapsed (handle both nanosecond and second precision)
if [ ${#START_TIME} -gt 10 ]; then
    ELAPSED=$(( (END_TIME - START_TIME) / 1000000 ))
    ELAPSED_STR="${ELAPSED}ms"
else
    ELAPSED=$(( END_TIME - START_TIME ))
    ELAPSED_STR="${ELAPSED}s"
fi

printf "\n${BOLD}============================================================${RESET}\n"
printf "  ${BOLD}Results:${RESET} "
printf "${GREEN}${PASS} passed${RESET}  "
if [ "$FAIL" -gt 0 ]; then
    printf "${RED}${FAIL} failed${RESET}  "
else
    printf "${DIM}0 failed${RESET}  "
fi
if [ "$WARN" -gt 0 ]; then
    printf "${YELLOW}${WARN} warnings${RESET}  "
fi
printf "${DIM}(${TOTAL} total, ${ELAPSED_STR})${RESET}\n"

if [ "$FAIL" -eq 0 ]; then
    printf "  ${BOLD}${GREEN}>>> SMOKE TEST PASSED <<<${RESET}\n"
else
    printf "  ${BOLD}${RED}>>> SMOKE TEST FAILED <<<${RESET}\n"
    printf "  ${DIM}Run 'python3 tools/qa-check.py --verbose' for detailed diagnostics${RESET}\n"
fi
printf "${BOLD}============================================================${RESET}\n\n"

# Exit code
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
