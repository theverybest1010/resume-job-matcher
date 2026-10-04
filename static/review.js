(function(root) {
  function reviewedCoverage(data, decisions) {
    const matched = [], missing = [];
    for (const row of data.requirements) {
      const accepted = row.candidates.some((c, i) => decisions[JSON.stringify([row.uri, i])] === 'accepted');
      (row.matched || accepted ? matched : missing).push(row.skill);
    }
    const total = data.requirements.length;
    return {matched, missing, additional:data.additional, required_count:total,
      matched_count:matched.length, coverage:total ? Math.round(1000*matched.length/total)/10 : null};
  }
  if(typeof module !== 'undefined' && module.exports) module.exports={reviewedCoverage};
  else root.reviewedCoverage=reviewedCoverage;
})(globalThis);
