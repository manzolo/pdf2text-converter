#!/bin/bash

# Comprehensive API Test Suite
# Tests all features of the PDF2Text Converter

set -e

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
TEST_FILE="${TEST_FILE:-uploads/test.pdf}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

print_header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}$1${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

test_passed() {
    echo -e "${GREEN}✅ PASSED:${NC} $1"
    ((PASSED++))
}

test_failed() {
    echo -e "${RED}❌ FAILED:${NC} $1"
    ((FAILED++))
}

# Check prerequisites
print_header "Checking Prerequisites"

if [ ! -f "$TEST_FILE" ]; then
    echo -e "${RED}Error: Test file not found: $TEST_FILE${NC}"
    exit 1
fi
echo "✓ Test file found: $TEST_FILE"

if ! command -v curl &> /dev/null; then
    echo -e "${RED}Error: curl not found${NC}"
    exit 1
fi
echo "✓ curl found"

if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}Warning: jq not found (optional)${NC}"
fi

# Test 1: Health Check
print_header "Test 1: Health Check"
response=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/health")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" == "200" ]; then
    test_passed "Health check endpoint"
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
else
    test_failed "Health check endpoint (HTTP $http_code)"
fi

# Test 2: Status Endpoint
print_header "Test 2: API Status"
response=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/api/status")
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" == "200" ]; then
    test_passed "Status endpoint"
else
    test_failed "Status endpoint (HTTP $http_code)"
fi

# Test 3: Extract without filtering
print_header "Test 3: Extract Without Filtering"
response=$(curl -s -w "\n%{http_code}" -X POST \
    "$BACKEND_URL/api/extract?use_ocr=true&chunk_processing=false&language=eng&remove_repetitive=false&remove_copyright=false" \
    -F "file=@$TEST_FILE")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" == "200" ]; then
    success=$(echo "$body" | jq -r '.success' 2>/dev/null)
    if [ "$success" == "true" ]; then
        test_passed "Extraction without filtering"
        echo "$body" | jq '{filename, pages, total_chars}' 2>/dev/null
    else
        test_failed "Extraction without filtering (success=false)"
    fi
else
    test_failed "Extraction without filtering (HTTP $http_code)"
fi

# Test 4: Extract with filtering
print_header "Test 4: Extract With Filtering"
response=$(curl -s -w "\n%{http_code}" -X POST \
    "$BACKEND_URL/api/extract?use_ocr=true&chunk_processing=false&language=eng&remove_repetitive=true&remove_copyright=true" \
    -F "file=@$TEST_FILE")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" == "200" ]; then
    success=$(echo "$body" | jq -r '.success' 2>/dev/null)
    if [ "$success" == "true" ]; then
        test_passed "Extraction with filtering"
        echo "$body" | jq '{filename, pages, total_chars}' 2>/dev/null
    else
        test_failed "Extraction with filtering (success=false)"
    fi
else
    test_failed "Extraction with filtering (HTTP $http_code)"
fi

# Test 5: Different languages
print_header "Test 5: Multi-language Support"
for lang in eng ita fra deu spa; do
    response=$(curl -s -w "\n%{http_code}" -X POST \
        "$BACKEND_URL/api/extract?language=$lang&chunk_processing=false" \
        -F "file=@$TEST_FILE")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" == "200" ]; then
        success=$(echo "$body" | jq -r '.success' 2>/dev/null)
        if [ "$success" == "true" ]; then
            test_passed "Language: $lang"
        else
            test_failed "Language: $lang (success=false)"
        fi
    else
        test_failed "Language: $lang (HTTP $http_code)"
    fi
done

# Test 6: OCR toggle
print_header "Test 6: OCR Toggle"
for ocr in true false; do
    response=$(curl -s -w "\n%{http_code}" -X POST \
        "$BACKEND_URL/api/extract?use_ocr=$ocr&chunk_processing=false" \
        -F "file=@$TEST_FILE")
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" == "200" ]; then
        test_passed "OCR=$ocr"
    else
        test_failed "OCR=$ocr (HTTP $http_code)"
    fi
done

# Test 7: Chunk processing
print_header "Test 7: Chunk Processing"
for chunk in true false; do
    response=$(curl -s -w "\n%{http_code}" -X POST \
        "$BACKEND_URL/api/extract?chunk_processing=$chunk" \
        -F "file=@$TEST_FILE")
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" == "200" ]; then
        test_passed "Chunk processing=$chunk"
    else
        test_failed "Chunk processing=$chunk (HTTP $http_code)"
    fi
done

# Test 8: Error handling - Non-PDF file
print_header "Test 8: Error Handling"
echo "test" > /tmp/test.txt
response=$(curl -s -w "\n%{http_code}" -X POST \
    "$BACKEND_URL/api/extract" \
    -F "file=@/tmp/test.txt")
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" == "400" ]; then
    test_passed "Non-PDF rejection"
else
    test_failed "Non-PDF rejection (expected 400, got $http_code)"
fi
rm /tmp/test.txt

# Test 9: Filtering comparison
print_header "Test 9: Filtering Effectiveness"
response1=$(curl -s -X POST \
    "$BACKEND_URL/api/extract?remove_repetitive=false&remove_copyright=false" \
    -F "file=@$TEST_FILE")
chars1=$(echo "$response1" | jq -r '.total_chars' 2>/dev/null || echo "0")

response2=$(curl -s -X POST \
    "$BACKEND_URL/api/extract?remove_repetitive=true&remove_copyright=true" \
    -F "file=@$TEST_FILE")
chars2=$(echo "$response2" | jq -r '.total_chars' 2>/dev/null || echo "0")

if [ "$chars1" != "0" ] && [ "$chars2" != "0" ]; then
    saved=$((chars1 - chars2))
    percent=$(echo "scale=1; ($saved * 100) / $chars1" | bc 2>/dev/null || echo "0")
    echo "Original: $chars1 chars"
    echo "Filtered: $chars2 chars"
    echo "Saved: $saved chars ($percent%)"
    if [ "$chars2" -le "$chars1" ]; then
        test_passed "Filtering reduces or maintains character count"
    else
        test_failed "Filtering increased character count"
    fi
else
    test_failed "Filtering comparison (invalid response)"
fi

# Summary
print_header "Test Summary"
echo ""
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
