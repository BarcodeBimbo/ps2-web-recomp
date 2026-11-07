"use strict";
const fs = require("fs");
const t = fs.readFileSync("C:/Program Files/cursor/resources/app/product.json", "utf8");
const m = t.match(/\n(\s+)"version"/);
console.log(
  JSON.stringify(
    {
      starts: t.slice(0, 40),
      hasTab: t.includes("\t"),
      indent: m ? m[1] : null,
      ends: t.slice(-30),
    },
    null,
    2
  )
);
