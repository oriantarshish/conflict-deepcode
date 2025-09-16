/**
 * Conflict DeepCode Installation Script
 * Handles Python dependencies and automatic Ollama installation
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const packageDir = path.dirname(__dirname);
const requirementsFile = path.join(packageDir, 'requirements.txt');
const OllamaInstaller = require('./auto-install-ollama');

console.log('🚀 Installing Conflict DeepCode...');

// Check if requirements.txt exists
if (!fs.existsSync(requirementsFile)) {
    console.log('⚠️  requirements.txt not found, skipping Python dependencies');
    return;
}

// Find Python command
function findPythonCmd() {
    return new Promise((resolve, reject) => {
        const pythonCmds = process.platform === 'win32'
            ? ['python', 'py']
            : ['python3', 'python'];

        let triedCmds = 0;

        function tryNext() {
            if (triedCmds >= pythonCmds.length) {
                reject(new Error('Python not found. Please install Python 3.8+'));
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

// Install Python dependencies
async function installPythonDeps() {
    try {
        const pythonCmd = await findPythonCmd();

        console.log('📦 Installing Python dependencies...');

        return new Promise((resolve) => {
            const pip = spawn(pythonCmd, ['-m', 'pip', 'install', '-r', requirementsFile], {
                stdio: 'inherit',
                cwd: packageDir
            });

            pip.on('close', (code) => {
                if (code === 0) {
                    console.log('✅ Python dependencies installed successfully');
                    resolve();
                } else {
                    console.log('⚠️  Failed to install some Python dependencies');
                    console.log('You may need to install them manually:');
                    console.log(`pip install -r ${requirementsFile}`);
                    resolve(); // Don't fail the installation
                }
            });

            pip.on('error', (error) => {
                console.log('⚠️  Error installing Python dependencies:', error.message);
                console.log('You may need to install them manually:');
                console.log(`pip install -r ${requirementsFile}`);
                resolve(); // Don't fail the installation
            });
        });
    } catch (error) {
        console.log('⚠️  Python not found, skipping Python dependencies');
        console.log('You may need to install Python 3.8+ and dependencies manually:');
        console.log(`pip install -r ${requirementsFile}`);
    }
}

// Setup Ollama automatically
async function setupOllama() {
    console.log('\n🤖 Setting up Ollama automatically...');
    const installer = new OllamaInstaller();
    return await installer.setup();
}

// Main installation
async function main() {
    try {
        // Install Python dependencies
        await installPythonDeps();
        
        // Setup Ollama automatically
        const ollamaSuccess = await setupOllama();
        
        if (ollamaSuccess) {
            console.log('\n🎉 Conflict DeepCode installation completed successfully!');
            console.log('Everything is ready to use:');
            console.log('• Run "dpcd" for quick chatbox access');
            console.log('• Run "deepcode" for full CLI');
            console.log('• Run "deepcode --help" to see all commands');
        } else {
            console.log('\n✅ Conflict DeepCode installation completed!');
            console.log('⚠️  Ollama setup failed, but you can still use the tool');
            console.log('\n📋 Manual setup required:');
            console.log('1. Install Ollama from https://ollama.ai');
            console.log('2. Run: ollama serve');
            console.log('3. Run: ollama pull deepseek-coder-v2');
            console.log('4. Try: dpcd or deepcode --help');
        }
        
    } catch (error) {
        console.error('❌ Installation failed:', error.message);
        process.exit(1);
    }
}

main();
