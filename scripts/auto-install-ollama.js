/**
 * Automatic Ollama Installation Script
 * Downloads and installs Ollama automatically
 */

const { spawn, exec } = require('child_process');
const https = require('https');
const fs = require('fs');
const path = require('path');
const os = require('os');

const packageDir = path.dirname(__dirname);

console.log('🤖 Setting up Ollama for Conflict DeepCode...');

// Platform-specific Ollama installation
class OllamaInstaller {
    constructor() {
        this.platform = process.platform;
        this.arch = process.arch;
        this.ollamaPath = this.getOllamaPath();
    }

    getOllamaPath() {
        return 'ollama';
    }

    async isOllamaInstalled() {
        return new Promise((resolve) => {
            const cmd = this.platform === 'win32' ? 'where ollama' : 'which ollama';
            exec(cmd, (error) => {
                resolve(!error);
            });
        });
    }

    async downloadOllama() {
        console.log('📥 Downloading Ollama...');
        
        if (this.platform === 'win32') {
            return this.downloadOllamaWindows();
        } else if (this.platform === 'darwin') {
            return this.downloadOllamaMac();
        } else {
            return this.downloadOllamaLinux();
        }
    }

    async downloadOllamaWindows() {
        return new Promise((resolve, reject) => {
            const installerUrl = 'https://github.com/ollama/ollama/releases/latest/download/OllamaSetup.exe';
            const installerPath = path.join(os.tmpdir(), 'OllamaSetup.exe');

            console.log('📥 Downloading Ollama installer for Windows...');

            const file = fs.createWriteStream(installerPath);
            https.get(installerUrl, (response) => {
                if (response.statusCode !== 200) {
                    reject(new Error(`Failed to download: ${response.statusCode}`));
                    return;
                }
                response.pipe(file);
                file.on('finish', () => {
                    file.close();
                    console.log('✅ Ollama installer downloaded');
                    resolve(installerPath);
                });
            }).on('error', (err) => {
                fs.unlink(installerPath, () => {});
                reject(err);
            });
        });
    }

    async downloadOllamaMac() {
        return new Promise((resolve, reject) => {
            const script = `
                curl -fsSL https://ollama.ai/install.sh | sh
            `;
            
            exec(script, (error, stdout, stderr) => {
                if (error) {
                    reject(error);
                } else {
                    console.log('✅ Ollama installed on macOS');
                    resolve();
                }
            });
        });
    }

    async downloadOllamaLinux() {
        return new Promise((resolve, reject) => {
            const script = `
                curl -fsSL https://ollama.ai/install.sh | sh
            `;
            
            exec(script, (error, stdout, stderr) => {
                if (error) {
                    reject(error);
                } else {
                    console.log('✅ Ollama installed on Linux');
                    resolve();
                }
            });
        });
    }

    async installOllama() {
        try {
            const isInstalled = await this.isOllamaInstalled();
            
            if (isInstalled) {
                console.log('✅ Ollama is already installed');
                return true;
            }

            if (this.platform === 'win32') {
                const installerPath = await this.downloadOllama();
                console.log('🚀 Installing Ollama...');
                
                return new Promise((resolve, reject) => {
                    const installer = spawn(installerPath, ['/S'], {
                        stdio: 'inherit'
                    });
                    
                    installer.on('close', (code) => {
                        if (code === 0) {
                            console.log('✅ Ollama installed successfully');
                            resolve(true);
                        } else {
                            reject(new Error('Ollama installation failed'));
                        }
                    });
                });
            } else {
                await this.downloadOllama();
                return true;
            }
        } catch (error) {
            console.log('⚠️  Failed to install Ollama automatically:', error.message);
            console.log('Please install Ollama manually from https://ollama.ai');
            return false;
        }
    }

    async startOllamaService() {
        console.log('🚀 Starting Ollama service...');

        return new Promise((resolve) => {
            // Start Ollama in background
            const ollama = spawn('ollama', ['serve'], {
                detached: true,
                stdio: 'ignore'
            });

            ollama.unref();

            // Wait a bit for service to start
            setTimeout(() => {
                console.log('✅ Ollama service started');
                resolve(true);
            }, 3000);
        });
    }

    async downloadModel() {
        console.log('📥 Downloading DeepSeek Coder V2 model...');
        console.log('This may take a few minutes depending on your internet connection...');

        return new Promise((resolve, reject) => {
            const pull = spawn('ollama', ['pull', 'deepseek-coder-v2'], {
                stdio: 'inherit'
            });

            pull.on('close', (code) => {
                if (code === 0) {
                    console.log('✅ DeepSeek Coder V2 model downloaded successfully');
                    resolve(true);
                } else {
                    reject(new Error('Failed to download model'));
                }
            });

            pull.on('error', (error) => {
                reject(error);
            });
        });
    }

    async setup() {
        try {
            console.log('🔧 Setting up Ollama for Conflict DeepCode...');
            
            // Install Ollama
            const installed = await this.installOllama();
            if (!installed) {
                return false;
            }
            
            // Start service
            await this.startOllamaService();
            
            // Download model
            await this.downloadModel();
            
            console.log('🎉 Ollama setup completed successfully!');
            return true;
            
        } catch (error) {
            console.error('❌ Ollama setup failed:', error.message);
            return false;
        }
    }
}

// Main installation function
async function main() {
    const installer = new OllamaInstaller();
    const success = await installer.setup();
    
    if (success) {
        console.log('\n✅ Conflict DeepCode is now fully ready!');
        console.log('You can now use: dpcd or deepcode');
    } else {
        console.log('\n⚠️  Ollama setup failed, but you can still use Conflict DeepCode');
        console.log('Please install Ollama manually from https://ollama.ai');
        console.log('Then run: ollama serve && ollama pull deepseek-coder-v2');
    }
}

if (require.main === module) {
    main();
}

module.exports = OllamaInstaller;
