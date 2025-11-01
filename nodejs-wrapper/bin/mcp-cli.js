#!/usr/bin/env node

const { executeMcpCli } = require('../index');

async function main() {
  try {
    const args = process.argv.slice(2);
    const result = await executeMcpCli(args);
    process.exit(result.code);
  } catch (error) {
    console.error('Error executing mcp-cli:', error.message);
    process.exit(1);
  }
}

main();