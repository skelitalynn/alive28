
function computeDayIndex(startStr, currentStr) {
  const [sy, sm, sd] = startStr.split("-").map(Number);
  const [ty, tm, td] = currentStr.split("-").map(Number);
  // Simulating the bug: using local time (system timezone)
  const s = new Date(sy, sm - 1, sd);
  const t = new Date(ty, tm - 1, td);
  const diff = Math.floor((t.getTime() - s.getTime()) / (24 * 3600 * 1000));
  return diff + 1;
}

// Test case: Standard Time to DST (Spring Forward)
// Example: New York, March 2024. DST starts March 10.
// Start: March 1 (Std). End: March 15 (DST).
// Days should be 15? (1..15). 15-1 = 14 days diff.
// Let's set the environment timezone to America/New_York if possible, or just mock it carefully?
// Node usually uses system timezone. I can't easily change system timezone.
// But I can observe if the math holds in general.

// Actually, let's try to simulate checking the math directly:
// If duration is (Days * 24 - 1) hours.
// (Days - 1/24) encoded.
// Math.floor(Days - 0.0416) = Days - 1 (if strict integer math? No. 14.95 -> 14. Correct is 14?)
// Wait. 
// March 1 to March 2 is 1 day. Diff 1 * 24h.
// March 9 to March 10 (DST switch at 2am).
// March 9 00:00 to March 10 00:00.
// If DST starts at 2am, March 10 00:00 is still Standard time? Or does day start shift?
// Usually clocks jump forward at 2am. So 00:00 to 00:00 is 24h?
// No, 00:00 is fine. 01:59 -> 03:00.
// So 00:00 to 00:00 next day is 23h if switch happens that day?
// Yes, the day of switch has 23 hours.
// So logs from Mar 9 00:00 to Mar 10 00:00 might be 24h?
// Wait, if switch is Mar 10. Mar 10 has 23h.
// Mar 10 00:00 to Mar 11 00:00 is 23h.
// Diff (Mar 11 - Mar 10) should be 1 day.
// (23 * 3600 * 1000) / (24 * 3600 * 1000) = 23/24 = 0.958.
// Math.floor(0.958) = 0.
// Expectation: Day 2 (diff 1 + 1). Result: Day 1 (diff 0 + 1).
// ERROR!

console.log("Testing Date Logic...");
// We can't easily force timezone here, but we can math it out.
const h23 = 23 * 3600 * 1000;
const h24 = 24 * 3600 * 1000;
const diffDays = Math.floor(h23 / h24);
console.log(`23 hours diff floor: ${diffDays} (Expected 1 day difference roughly?)`);
// If we are strictly counting calendar days, it should be 1.
// But code returns 0.

const h25 = 25 * 3600 * 1000;
const diffDays25 = Math.floor(h25 / h24);
console.log(`25 hours diff floor: ${diffDays25} (Expected 1 day diff)`);
// Returns 1. Correct.

console.log("Conclusion: Math.floor on DST 'short days' causes off-by-one errors.");
