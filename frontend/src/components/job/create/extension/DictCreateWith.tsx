/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect } from "react"
import * as Blockly from "blockly/core"


type DictItemMutatorBlock = Blockly.Block & {
  keyConnection_?: Blockly.Connection | null;
  valueConnection_?: Blockly.Connection | null;
};

type DictCreateWith = Blockly.Block & {
  itemCount_: number;
  updateShape_: () => void;
};

const DICT_CREATE_WITH_MUTATOR_MIXIN = {
  itemCount_: 2,

  saveExtraState: function (this: DictCreateWith) {
    return {
      itemCount: this.itemCount_,
    };
  },

  loadExtraState: function (this: DictCreateWith, state: { itemCount?: number }): void {
    this.itemCount_ = state.itemCount || 0;
    this.updateShape_();
  },

  decompose: function (this: DictCreateWith, workspace: Blockly.WorkspaceSvg): Blockly.Block {
    const containerBlock = workspace.newBlock('dict_create_with_container');
    containerBlock.initSvg?.();
    containerBlock.render?.();
    let connection = containerBlock.getInput('STACK')?.connection;
    if (!connection) return containerBlock;
    for (let i = 0; i < this.itemCount_; i++) {
      const itemBlock = workspace.newBlock('dict_create_with_item');
      itemBlock.initSvg?.();
      itemBlock.render?.();
      if (itemBlock.previousConnection) {
        connection.connect(itemBlock.previousConnection);
      }
      if (itemBlock.nextConnection) {
        connection = itemBlock.nextConnection;
      }
    }
    return containerBlock;
  },

  compose: function (this: DictCreateWith, containerBlock: Blockly.Block): void {
    let itemBlock = containerBlock.getInputTargetBlock('STACK') as DictItemMutatorBlock | null;
    const keyConnections: Array<Blockly.Connection | null | undefined> = [];
    const valueConnections: Array<Blockly.Connection | null | undefined> = [];
    while (itemBlock) {
      keyConnections.push(itemBlock.keyConnection_);
      valueConnections.push(itemBlock.valueConnection_);
      itemBlock = itemBlock.nextConnection?.targetBlock() as DictItemMutatorBlock | null;
    }
    for (let i = 0; i < this.itemCount_; i++) {
      const keyConn = this.getInput('KEY' + i)?.connection?.targetConnection;
      const valueConn = this.getInput('VALUE' + i)?.connection?.targetConnection;
      if (keyConn && !keyConnections.includes(keyConn)) {
        keyConn.disconnect();
      }
      if (valueConn && !valueConnections.includes(valueConn)) {
        valueConn.disconnect();
      }
    }
    this.itemCount_ = keyConnections.length;
    this.updateShape_();
    for (let i = 0; i < this.itemCount_; i++) {
      keyConnections[i]?.reconnect(this, 'KEY' + i);
      valueConnections[i]?.reconnect(this, 'VALUE' + i);
    }
  },

  saveConnections: function (this: DictCreateWith, containerBlock: Blockly.Block): void {
    let itemBlock = containerBlock.getInputTargetBlock('STACK') as DictItemMutatorBlock | null;
    let i = 0;
    while (itemBlock) {
      const keyInput = this.getInput('KEY' + i);
      const valueInput = this.getInput('VALUE' + i);
      itemBlock.keyConnection_ = keyInput?.connection?.targetConnection || null;
      itemBlock.valueConnection_ = valueInput?.connection?.targetConnection || null;
      i++;
      itemBlock = itemBlock.nextConnection?.targetBlock() as DictItemMutatorBlock | null;
    }
  },

  updateShape_: function (this: DictCreateWith): void {
    if (this.getInput('EMPTY')) {
      this.removeInput('EMPTY');
    }
    let i = 0;
    while (this.getInput('KEY' + i)) {
      this.removeInput('KEY' + i);
      if (this.getInput('VALUE' + i)) {
        this.removeInput('VALUE' + i);
      }
      i++;
    }
    if (this.itemCount_ === 0) {
      this.appendDummyInput('EMPTY').appendField('空の辞書を作成');
    } else {
      for (let index = 0; index < this.itemCount_; index++) {
        this.appendValueInput('KEY' + index)
          .setAlign(Blockly.inputs.Align.RIGHT)
          .appendField(index === 0 ? '辞書を作成：' : '')
          .appendField('索引');
        this.appendValueInput('VALUE' + index)
          .setAlign(Blockly.inputs.Align.RIGHT)
          .appendField('└値');
      }
    }
  },
};

const DICT_CREATE_WITH_MUTATOR_EXTENSION = function (this: DictCreateWith) {
  this.itemCount_ = 2;
  this.updateShape_();
};

export function RegisterDictCreateWithBlock() {
  useEffect(() => {
    Blockly.defineBlocksWithJsonArray([
      {
        type: "dict_create_with_container",
        message0: "辞書",
        message1: "%1",
        args1: [
          {
            type: "input_statement",
            name: "STACK",
          },
        ],
        colour: 280
      },
      {
        type: "dict_create_with_item",
        message0: "%{BKY_LISTS_CREATE_WITH_ITEM_TITLE}",
        previousStatement: null,
        nextStatement: null,
        colour: 280,
      },
    ])
    Blockly.Extensions.registerMutator(
      "dict_create_with_mutator",
      DICT_CREATE_WITH_MUTATOR_MIXIN,
      DICT_CREATE_WITH_MUTATOR_EXTENSION,
      ["dict_create_with_item"]
    )

    return () => {
      delete Blockly.Blocks["dict_create_with_container"]
      delete Blockly.Blocks["dict_create_with_item"]
      Blockly.Extensions.unregister("dict_create_with_mutator")
    };
  }, []);

  return <></>
}
