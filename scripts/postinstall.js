/**
 * Conflict DeepCode Post-Installation Script
 * Performs final setup tasks
 */

const path = require('path');
const fs = require('fs');
const os = require('os');

const packageDir = path.dirname(__dirname);

console.log('🔧 Setting up Conflict DeepCode...');

// Create global config directory
function createConfigDir() {
    const configDir = path.join(os.homedir(), '.conflict-deepcode');
    
    if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
        console.log('📁 Created config directory:', configDir);
    }
}

// Create default config file
function createDefaultConfig() {
    const configDir = path.join(os.homedir(), '.conflict-deepcode');
    const configFile = path.join(configDir, 'config.yaml');
    
    if (!fs.existsSync(configFile)) {
        const defaultConfig = `# Conflict DeepCode Configuration
ollama:
  host: http://localhost:11434
  model: deepseek-coder-v2
  timeout: 120
  num_ctx: 32768
  num_predict: 2048
  temperature: 0.2
  top_p: 0.9

agent:
  use_optimized: true
  enable_caching: true
  enable_streaming: true
  parallel_analysis: true
  max_context_length: 32768
  cache_ttl_minutes: 15
  max_conversation_history: 50
  enable_dangerous_action_confirmation: true

editor:
  default: code
  backup: true
  auto_format: true
  smart_suggestions: true

project:
  ignore_patterns:
    - .git
    - node_modules
    - __pycache__
    - "*.pyc"
    - .conflict-deepcode
  max_file_size: 5MB
  context_lines: 100
  auto_analyze_on_edit: true

ui:
  color_scheme: dark
  show_progress: true
  verbose_errors: false
  typing_animation: true
  show_performance_stats: true

performance:
  enable_profiling: false
  log_response_times: true
  optimize_for_speed: true
  memory_limit_mb: 1024
`;
        
        fs.writeFileSync(configFile, defaultConfig);
        console.log('⚙️  Created default config file:', configFile);
    }
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
                reject(new Error('Python not found'));
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

// Check Python installation
async function checkPython() {
    try {
        const pythonCmd = await findPythonCmd();
        console.log('✅ Python is available');
        return true;
    } catch (error) {
        console.log('⚠️  Python not found. Please install Python 3.8+');
        return false;
    }
}

// Main post-installation
async function main() {
    try {
        createConfigDir();
        createDefaultConfig();
        
        const pythonAvailable = await checkPython();
        
        if (pythonAvailable) {
            console.log('✅ Conflict DeepCode setup completed successfully!');
        } else {
            console.log('⚠️  Conflict DeepCode setup completed, but Python is required for full functionality');
        }
        
        console.log('\n🎉 Conflict DeepCode is ready to use!');
        console.log('Run "deepcode --help" to see available commands');
        
    } catch (error) {
        console.error('❌ Post-installation setup failed:', error.message);
    }
}

main();
