const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const WasmPackPlugin = require('@wasm-tool/wasm-pack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');

module.exports = {
  entry: './frontend/src/index.js',
  output: {
    path: path.resolve(__dirname, 'frontend/dist'),
    filename: 'bundle.[contenthash].js',
    clean: true,
  },
  mode: 'development',
  devtool: 'source-map',
  
  devServer: {
    static: {
      directory: path.join(__dirname, 'frontend/dist'),
    },
    compress: true,
    port: 3000,
    hot: true,
    historyApiFallback: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        pathRewrite: {
          '^/api': ''
        }
      }
    }
  },

  plugins: [
    new HtmlWebpackPlugin({
      template: './frontend/public/index.html',
      title: 'Hegel Biological Computing Platform'
    }),
    
    new WasmPackPlugin({
      crateDirectory: path.resolve(__dirname, 'src/wasm/frontend-bindings'),
      outDir: path.resolve(__dirname, 'frontend/pkg'),
      outName: 'hegel_biological_computing',
      extraArgs: '--target web',
      forceMode: 'production',
      pluginLogLevel: 'info'
    }),
    
    new CopyWebpackPlugin({
      patterns: [
        {
          from: path.resolve(__dirname, 'frontend/public'),
          to: path.resolve(__dirname, 'frontend/dist'),
          globOptions: {
            ignore: ['**/index.html']
          }
        }
      ]
    })
  ],

  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              ['@babel/preset-env', {
                targets: {
                  browsers: ['> 1%', 'last 2 versions']
                },
                modules: false
              }]
            ],
            plugins: [
              '@babel/plugin-syntax-dynamic-import',
              '@babel/plugin-proposal-async-generator-functions'
            ]
          }
        }
      },
      
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/
      },
      
      {
        test: /\.css$/i,
        use: ['style-loader', 'css-loader', 'postcss-loader']
      },
      
      {
        test: /\.scss$/i,
        use: ['style-loader', 'css-loader', 'sass-loader']
      },
      
      {
        test: /\.(png|svg|jpg|jpeg|gif|ico)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'assets/images/[name].[contenthash][ext]'
        }
      },
      
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'assets/fonts/[name].[contenthash][ext]'
        }
      },
      
      {
        test: /\.wasm$/,
        type: 'webassembly/async'
      }
    ]
  },

  resolve: {
    extensions: ['.tsx', '.ts', '.js', '.wasm'],
    alias: {
      '@': path.resolve(__dirname, 'frontend/src'),
      '@pkg': path.resolve(__dirname, 'frontend/pkg'),
      '@components': path.resolve(__dirname, 'frontend/src/components'),
      '@utils': path.resolve(__dirname, 'frontend/src/utils'),
      '@biological': path.resolve(__dirname, 'frontend/src/biological')
    }
  },

  experiments: {
    asyncWebAssembly: true,
    topLevelAwait: true
  },

  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all'
        },
        wasm: {
          test: /\.wasm$/,
          name: 'wasm',
          chunks: 'all'
        }
      }
    }
  }
};

// Production configuration
if (process.env.NODE_ENV === 'production') {
  module.exports.mode = 'production';
  module.exports.devtool = false;
  
  // Additional production optimizations
  const TerserPlugin = require('terser-webpack-plugin');
  const CompressionPlugin = require('compression-webpack-plugin');
  
  module.exports.optimization = {
    ...module.exports.optimization,
    minimize: true,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: true
          }
        }
      })
    ]
  };
  
  module.exports.plugins.push(
    new CompressionPlugin({
      filename: '[path][base].gz',
      algorithm: 'gzip',
      test: /\.(js|css|html|svg|wasm)$/,
      threshold: 8192,
      minRatio: 0.8
    })
  );
}
