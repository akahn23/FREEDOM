/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

"use client";
import { useCallback, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { useTranslations } from "next-intl";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
} from "@mui/material";
import { Close } from "@mui/icons-material";
import { useDialogs, DialogProps } from '@toolpad/core/useDialogs';
import * as Blockly from "blockly/core";
import { Area, AreaGeoJSON } from "@/components/map/MapDraw";

const MapView = dynamic(() => import("@/components/map/MapView"), { ssr: false });
const MapDraw = dynamic(() => import("@/components/map/MapDraw"), { ssr: false });


type AreaDialogFn = (currentValue: Area[]) => Promise<Area[]>;

export class FieldArea extends Blockly.Field<Area[]> {
  private static openDialog: AreaDialogFn | null = null;
  override SERIALIZABLE = true;

  constructor(value?: Area[]) {
    super(value ?? []);
  }

  static setOpenDialog(fn: AreaDialogFn) {
    FieldArea.openDialog = fn;
  }

  static fromJson(options: Blockly.FieldConfig & { value?: Area[] }) {
    return new FieldArea(options.value ?? []);
  }

  getText() {
    const value = this.getValue();
    const areas = typeof value === "string" ? JSON.parse(value) : value;
    if (!areas || areas.length === 0) {
      return "エリア未設定";
    }
    return `${areas.length}エリア`;
  }

  override showEditor_() {
    if (!FieldArea.openDialog) {
      console.warn('FieldArea.openDialog is not set');
      return;
    }
    FieldArea.openDialog(this.getValue() ?? [])
      .then((newValue) => {
        if (newValue != null) {
          this.setValue(newValue);
        }
      })
      .catch((err) => {
        console.error('Dialog error:', err);
      });
  }
}

function geoJSONToAreaList(shapes: AreaGeoJSON[]): Area[] {
  return shapes.map((shape, index) => {
    const name = shape.properties?.name || `エリア ${index + 1}`;
    const vertexList = shape.geometry.coordinates[0].map(([lng, lat]) => {
      return [lat, lng];
    });
    return {
      name,
      vertex_list: vertexList,
    };
  });
}

function AreaDialog({ payload, open, onClose }: DialogProps<Area[], Area[]>) {
  const [result, setResult] = useState(payload);
  const translate = useTranslations("Node.job.create");
  const handleChange = useCallback((shapes: AreaGeoJSON[]) => {
    setResult(geoJSONToAreaList(shapes));
  }, []);

  return (
    <Dialog
      fullWidth
      maxWidth="lg"
      open={open}
      onClose={() => onClose(result)}
      PaperProps={{
        sx: {
          height: "calc(100vh - 96px)",
          maxHeight: "820px",
        },
      }}
    >
      <DialogTitle>{translate("area.title")}</DialogTitle>
      <DialogContent
        dividers
        sx={{
          p: 0,
          display: "flex",
          flexDirection: "column",
          minHeight: 0,
          overflow: "hidden",
        }}
      >
        <MapView style={{ width: "100%", height: "100%" }}>
          <MapDraw
            initialShapes={payload}
            onChange={handleChange}
          />
        </MapView>
      </DialogContent>
      <DialogActions sx={{ justifyContent: "flex-end", px: 2, py: 1 }}>
        <Button
          variant="outlined"
          color="primary"
          startIcon={<Close />}
          onClick={() => {onClose(result)}}
        >
          {translate("area.close")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export function RegisterFieldArea() {
  const dialogs = useDialogs();

  useEffect(() => {
    Blockly.fieldRegistry.register("field_area", FieldArea);
    return () => {
      Blockly.fieldRegistry.unregister("field_area");
    };
  }, []);

  useEffect(() => {
    FieldArea.setOpenDialog(async (currentValue: Area[]) => {
      return await dialogs.open(AreaDialog, currentValue);
    });
  }, [dialogs]);

  return <></>
}
