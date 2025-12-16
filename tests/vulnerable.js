/**
 * Test file with intentional vulnerabilities for ESLint scanning
 */

// Security: eval usage (code injection)
function dangerousEval(userInput) {
    eval(userInput);
}

// Security: Unsafe regex (ReDoS)
const unsafeRegex = /(a+)+$/;

// No-unsanitized: DOM XSS
function updateDOM(userContent) {
    document.body.innerHTML = userContent;
}

// Security: Detect non-literal require
function dynamicRequire(moduleName) {
    require(moduleName);
}

// Security: Detect unsafe randomness
function weakRandom() {
    return Math.random();
}

// Security: Detect buffer usage
const buf = new Buffer(100);

// Export for testing
module.exports = {
    dangerousEval,
    updateDOM,
    dynamicRequire,
    weakRandom
};
