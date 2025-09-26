import { EditorView, basicSetup } from 'codemirror'

import {
  keymap, drawSelection, highlightActiveLine, dropCursor,
  lineNumbers, highlightActiveLineGutter
} from "@codemirror/view"
import {
  indentOnInput, bracketMatching, foldGutter, foldKeymap
} from "@codemirror/language"
import {
  defaultKeymap, history, historyKeymap, indentWithTab
} from "@codemirror/commands"
import {
  searchKeymap, 
} from "@codemirror/search"
import {
  autocompletion, completionKeymap, closeBrackets,
  closeBracketsKeymap
} from "@codemirror/autocomplete"
import {yaml} from "@codemirror/lang-yaml"

import { basicDark } from '@fsegurai/codemirror-theme-basic-dark'


const view = null;

const defaultText = `
var:
  pre: skadis
then:
  - base: input/base-40-7.stl
  - load: input/base-40-7.stl
  - offset: [40, 0, 0]
  - rebase: true
  - load: input/cube.stl
  - set_size: [47, 2, 40]
  - attach: top_center
  - offset: [0, -2, 0]
  - iterate:
    - label: lower
      x: -15
      z: 10
    - label: upper
      x: 15
      z: 11
    then:
      - print: {eval: label}
      - sleep: 2
      - load: input/cube.stl
      - set_size: [47, 6, 10]
      - attach: top_center
      - offset:
          eval: [0, -2, z]
      - load: input/wedge.stl
      - set_size: [47, 4, 4]
      - attach: top_center
      - offset: 
          eval: [0, 0, z + 7]
      - load: input/wedge.stl
      - set_size: [47, 4, 4]
      - rotate_y: 180
      - attach: top_center
      - offset: 
          eval: [0, 0, z - 7]
      - load: input/cylinder.stl
      - rotate_x: 90
      - set_size: [3, 8, 3]
      - attach: top_center
      - offset: 
          eval: [x, 0, z]
      - load: input/cylinder.stl
      - rotate_x: 90
      - set_size: [8, 1, 8]
      - attach: top_center
      - offset: 
          eval: [x, 8, z]
      - save_as: '{pre}-outlet-{label}.stl'
`;

export class Editor {
  view: EditorView;

  constructor(customKeyMap) {
    if (customKeyMap === undefined) customKeyMap = [];
    this.view = new EditorView({
      doc: defaultText.trim(),
      parent: document.getElementById('editor'),
      extensions: [
        basicSetup,
        // A line number gutter
        lineNumbers(),
        // A gutter with code folding markers
        foldGutter(),
        // // Replace non-printable characters with placeholders
        // highlightSpecialChars(),
        // The undo history
        history(),
        // Replace native cursor/selection with our own
        drawSelection(),
        // Show a drop cursor when dragging over the editor
        dropCursor(),
        // Allow multiple cursors/selections
        // EditorState.allowMultipleSelections.of(true),
        // Re-indent lines when typing specific input
        indentOnInput(),
        // Highlight syntax with a default style
        // syntaxHighlighting(defaultHighlightStyle),
        // Highlight matching brackets near cursor
        bracketMatching(),
        // Automatically close brackets
        closeBrackets(),
        // Load the autocompletion system
        autocompletion(),
        // Allow alt-drag to select rectangular regions
        // rectangularSelection(),
        // Change the cursor to a crosshair when holding alt
        // crosshairCursor(),
        // Style the current line specially
        highlightActiveLine(),
        // Style the gutter for current line specially
        highlightActiveLineGutter(),
        // Highlight text that matches the selected text
        // highlightSelectionMatches(),
        keymap.of([
          ...customKeyMap,
          // Closed-brackets aware backspace
          ...closeBracketsKeymap,
          // A large set of basic bindings
          ...defaultKeymap,
          // Search-related keys
          ...searchKeymap,
          // Redo/undo keys
          ...historyKeymap,
          // Code folding bindings
          ...foldKeymap,
          // Autocompletion keys
          ...completionKeymap,
          indentWithTab,
        ]),
        yaml(),
        basicDark,
      ]
    });
  }

  getText() {
    return this.view.state.doc.toString();
  }
}
