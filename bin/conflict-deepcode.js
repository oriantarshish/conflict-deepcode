#!/usr/bin/env node

/**
 * conflict-deepcode CLI Entry Point
 * This script handles the npm package installation and delegates to the Python CLI
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Get the directory where this package is installed
const packageDir = path.dirname(__dirname);
const pythonScript = path.join(packageDir, 'src', 'main.py');

// Check if Python is available
function checkPython() {
    return new Promise((resolve, reject) => {
        const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
        const check = spawn(pythonCmd, ['--version'], { stdio: 'pipe' });
        
        check.on('close', (code) => {
            if (code === 0) {
                resolve(pythonCmd);
            } else {
                // Try alternative Python commands
                const altCmd = process.platform === 'win32' ? 'py' : 'python';
                const altCheck = spawn(altCmd, ['--version'], { stdio: 'pipe' });
                
                altCheck.on('close', (altCode) => {
                    if (altCode === 0) {
                        resolve(altCmd);
                    } else {
                        reject(new Error('Python not found. Please install Python 3.8+ to use DeepCode.'));
                    }
                });
            }
        });
    });
}

// Check if the Python script exists
function checkScript() {
    if (!fs.existsSync(pythonScript)) {
        console.error('❌ conflict-deepcode Python script not found. Please reinstall the package.');
        process.exit(1);
    }
}

// Main function
async function main() {
    try {
        // Check if Python script exists
        checkScript();
        
        // Check if Python is available
        const pythonCmd = await checkPython();
        
        // Get command line arguments
        const args = process.argv.slice(2);
        
        // If no arguments provided, launch the beautiful UI
        if (args.length === 0) {
            console.log('🚀 Launching Conflict DeepCode...');
        }
        
        // Spawn Python process
        const pythonProcess = spawn(pythonCmd, [pythonScript, ...args], {
            stdio: 'inherit',
            cwd: process.cwd()
        });
        
        // Handle process events
        pythonProcess.on('close', (code) => {
            process.exit(code);
        });
        
        pythonProcess.on('error', (error) => {
            console.error('❌ Error running conflict-deepcode:', error.message);
            process.exit(1);
        });
        
    } catch (error) {
        console.error('❌', error.message);
        console.log('\n📋 Setup Instructions:');
        console.log('1. Install Python 3.8+ from https://python.org');
        console.log('2. Install Ollama from https://ollama.ai');
        console.log('3. Run: ollama serve');
        console.log('4. Run: ollama pull deepseek-coder-v2');
        console.log('5. Try: conflict-deepcode --help');
        process.exit(1);
    }
}

// Handle Ctrl+C gracefully
process.on('SIGINT', () => {
    console.log('\n👋 conflict-deepcode interrupted');
    process.exit(0);
});

// Run main function
main();
