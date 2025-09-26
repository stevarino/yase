import { nodeResolve } from '@rollup/plugin-node-resolve';
import terser from '@rollup/plugin-terser';

export default {
	input: './build/main.js',
	output: {
    file: '../web/rollup.js',
    format: 'cjs',
  },
	plugins: [nodeResolve(), terser()],
};
