const { executeMcpCli, isMcpCliInstalled } = require('../index');

async function runTests() {
  console.log('Running Node.js wrapper tests...\n');

  try {
    // Test 1: Check if mcp-cli is installed
    console.log('Test 1: Checking if mcp-cli is installed...');
    const isInstalled = await isMcpCliInstalled();
    console.log(`✅ Installation check completed: ${isInstalled ? 'installed' : 'not installed'}\n`);

    if (isInstalled) {
      // Test 2: Execute version command
      console.log('Test 2: Getting version...');
      const versionResult = await executeMcpCli(['--version'], { stdio: 'pipe' });
      console.log(`✅ Version command completed with exit code: ${versionResult.code}`);
      if (versionResult.stdout) {
        console.log(`   Output: ${versionResult.stdout.trim()}`);
      }
      console.log();

      // Test 3: Execute help command
      console.log('Test 3: Getting help...');
      const helpResult = await executeMcpCli(['--help'], { stdio: 'pipe' });
      console.log(`✅ Help command completed with exit code: ${helpResult.code}\n`);
    } else {
      console.log('⚠️  mcp-cli not installed, skipping execution tests');
      console.log('   Run: npm run postinstall');
      console.log('   Or: node scripts/install.js\n');
    }

    console.log('🎉 All tests completed successfully!');
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  runTests();
}

module.exports = { runTests };