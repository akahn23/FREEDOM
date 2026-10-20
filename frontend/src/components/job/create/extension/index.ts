/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import { RegisterDictCreateWithBlock } from "./DictCreateWith";
import { RegisterFieldArea } from "./FieldArea";
import { RegisterFieldLocation } from "./FieldLocation";
import { PlcGetAddress } from "./PlcGetAddress";

export const extensions = [
  RegisterDictCreateWithBlock,
  RegisterFieldArea,
  RegisterFieldLocation,
  PlcGetAddress,
];
