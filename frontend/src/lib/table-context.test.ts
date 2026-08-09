import { describe, expect, it } from "vitest";
import { parseTableNumber } from "@/lib/table-context";

describe("parseTableNumber", () => {
  it.each([["1", 1], ["42", 42], ["999", 999], [" 07 ", 7]])(
    "parses %s as a valid table",
    (value, expected) => expect(parseTableNumber(value)).toBe(expected),
  );

  it.each([null, undefined, "", "0", "1000", "12abc", "-1"])(
    "rejects invalid table value %s",
    (value) => expect(parseTableNumber(value)).toBeNull(),
  );
});
