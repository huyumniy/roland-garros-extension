const path = require("path");
const CopyPlugin = require("copy-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

module.exports = {
  entry: {
    content: "./src/content-scripts/content.js",
  },
  output: {
    path: path.resolve(__dirname, "dist/content-scripts"),
    filename: "[name].js",
    clean: true,
  },
  module: {
    rules: [
      {
        test: /\.css$/,
        use: [MiniCssExtractPlugin.loader, "css-loader"],
        include: path.resolve(__dirname, "ui"),
      },
      {
        test: /\.html$/,
        type: "asset/resource",
        generator: {
          filename: "ui/[name][ext]",
        },
        include: path.resolve(__dirname, "ui"),
      },
    ],
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: "content-scripts/ui/settings.css",
    }),
    new CopyPlugin({
      patterns: [{ from: "src/content-scripts/ui/settings.html", 
      to: "ui/settings.html" }],
    }),
  ],
  resolve: {
    extensions: [".js"],
  },
};
