#!/usr/bin/env node

/**
 * dpcd - DeepCode Chat Interface
 * A simple command that launches the interactive chatbox interface
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Get the directory where this package is installed
const packageDir = path.dirname(__dirname);
const pythonScript = path.join(packageDir, 'src', 'main.py');

// Check if Python is available
function checkPython() {
    return new Promise((resolve, reject) => {
        const pythonCmds = process.platform === 'win32'
            ? ['python', 'py']
            : ['python3', 'python'];

        let triedCmds = 0;

        function tryNext() {
            if (triedCmds >= pythonCmds.length) {
                reject(new Error('Python not found. Please install Python 3.8+ to use dpcd.'));
                return;
            }

            const cmd = pythonCmds[triedCmds++];
            const check = spawn(cmd, ['--version'], { stdio: 'pipe' });

            check.on('close', (code) => {
                if (code === 0) {
                    // On non-Windows, verify it's Python 3+
                    if (process.platform !== 'win32') {
                        const versionCheck = spawn(cmd, ['-c', 'import sys; print(sys.version_info[:2])'], { stdio: 'pipe' });
                        let versionOutput = '';

                        versionCheck.stdout.on('data', (data) => {
                            versionOutput += data.toString();
                        });

                        versionCheck.on('close', (versionCode) => {
                            if (versionCode === 0) {
                                try {
                                    const version = versionOutput.trim().replace(/[()]/g, '').split(',').map(x => parseInt(x.trim()));
                                    if (version[0] >= 3 && version[1] >= 8) {
                                        resolve(cmd);
                                    } else {
                                        console.log(`⚠️  ${cmd} is Python ${version[0]}.${version[1]}, need 3.8+. Trying alternatives...`);
                                        tryNext();
                                    }
                                } catch (e) {
                                    tryNext();
                                }
                            } else {
                                tryNext();
                            }
                        });
                    } else {
                        resolve(cmd);
                    }
                } else {
                    tryNext();
                }
            });

            check.on('error', () => {
                tryNext();
            });
        }

        tryNext();
    });
}

// Check if the Python script exists
function checkScript() {
    if (!fs.existsSync(pythonScript)) {
        console.error('❌ dpcd Python script not found. Please reinstall the package.');
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
        
        // Always launch the chatbox interface (ui command)
        // If user provides arguments, they'll be passed to the Python script
        const finalArgs = args.length > 0 ? args : ['ui'];
        
        console.log('🚀 Launching dpcd chatbox...');
        
        // Spawn Python process with ui command to launch the chatbox
        const pythonProcess = spawn(pythonCmd, [pythonScript, ...finalArgs], {
            stdio: 'inherit',
            cwd: process.cwd()
        });
        
        // Handle process events
        pythonProcess.on('close', (code) => {
            process.exit(code);
        });
        
        pythonProcess.on('error', (error) => {
            console.error('❌ Error running dpcd:', error.message);
            process.exit(1);
        });
        
    } catch (error) {
        console.error('❌', error.message);
        console.log('\n📋 Setup Instructions:');
        console.log('1. Install Python 3.8+ from https://python.org');
        console.log('2. Install Ollama from https://ollama.ai');
        console.log('3. Run: ollama serve');
        console.log('4. Run: ollama pull deepseek-coder-v2');
        console.log('5. Try: dpcd');
        process.exit(1);
    }
}

// Handle Ctrl+C gracefully
process.on('SIGINT', () => {
    console.log('\n👋 dpcd chatbox closed');
    process.exit(0);
});

// Run main function
main();
