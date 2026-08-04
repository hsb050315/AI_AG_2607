#!/usr/bin/env node
/**
 * Rank trivago accommodation search results by value-for-money (price + rating).
 *
 * Usage:
 *   node rank_accommodations.js <input.json> [--top N] [--min-reviews N]
 *
 * Input: a JSON file containing the trivago MCP tool's raw response (an
 * object with an "accommodations" array) or a bare array of accommodation
 * objects with the same fields (price_per_night, review_rating,
 * review_count, ...).
 *
 * Output (stdout): JSON array of the top N accommodations, sorted
 * best-value first, each with an added "value_rank" and "value_score"
 * (0-1, higher = better value). Listings with fewer than --min-reviews
 * reviews are kept but flagged "low_review_confidence": true and ranked
 * after every reliable listing, since a high score built on a handful of
 * reviews is not trustworthy enough to call "best value".
 */
const fs = require("fs");

function parsePrice(raw) {
  // Strip currency symbols/words, keep digits . and , e.g. '216,194 원' -> 216194
  const cleaned = String(raw).replace(/[^\d.,]/g, "").replace(/,/g, "");
  return parseFloat(cleaned);
}

function parseCount(raw) {
  const digits = String(raw ?? "0").replace(/[^\d]/g, "");
  return digits ? parseInt(digits, 10) : 0;
}

function main() {
  const args = process.argv.slice(2);
  const inputPath = args[0];
  if (!inputPath) {
    console.error("Usage: node rank_accommodations.js <input.json> [--top N] [--min-reviews N]");
    process.exit(1);
  }
  let top = 10;
  let minReviews = 10;
  for (let i = 1; i < args.length; i++) {
    if (args[i] === "--top") top = parseInt(args[++i], 10);
    if (args[i] === "--min-reviews") minReviews = parseInt(args[++i], 10);
  }

  const raw = JSON.parse(fs.readFileSync(inputPath, "utf-8"));
  const accommodations = Array.isArray(raw) ? raw : raw.accommodations || [];

  const parsed = [];
  for (const acc of accommodations) {
    const price = parsePrice(acc.price_per_night);
    const rating = parseFloat(acc.review_rating);
    if (Number.isNaN(price) || Number.isNaN(rating)) continue;
    parsed.push({ ...acc, _price: price, _rating: rating, _reviewCount: parseCount(acc.review_count) });
  }

  if (parsed.length === 0) {
    console.log(JSON.stringify([]));
    return;
  }

  const prices = parsed.map((a) => a._price);
  const ratings = parsed.map((a) => a._rating);
  const minP = Math.min(...prices);
  const maxP = Math.max(...prices);
  const minR = Math.min(...ratings);
  const maxR = Math.max(...ratings);

  for (const a of parsed) {
    const priceScore = maxP === minP ? 1 : (maxP - a._price) / (maxP - minP);
    const ratingScore = maxR === minR ? 1 : (a._rating - minR) / (maxR - minR);
    a.value_score = Math.round((0.5 * priceScore + 0.5 * ratingScore) * 10000) / 10000;
    a.low_review_confidence = a._reviewCount < minReviews;
  }

  parsed.sort((a, b) => {
    if (a.low_review_confidence !== b.low_review_confidence) {
      return a.low_review_confidence ? 1 : -1;
    }
    return b.value_score - a.value_score;
  });

  const result = parsed.slice(0, top).map((a, i) => {
    const { _price, _rating, _reviewCount, ...rest } = a;
    return { ...rest, value_rank: i + 1 };
  });

  console.log(JSON.stringify(result, null, 2));
}

main();
