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

// Install Python dependencies
function installPythonDeps() {
    return new Promise((resolve, reject) => {
        const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
        
        console.log('📦 Installing Python dependencies...');
        
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
