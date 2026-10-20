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
import { MarkerGeoJSON } from "@/components/map/MapDrawMarker";

const MapView = dynamic(() => import("@/components/map/MapView"), { ssr: false });
const MapDrawMarker = dynamic(() => import("@/components/map/MapDrawMarker"), { ssr: false });


type Location = [number, number];
type LocationDialogFn = (currentValue: Location) => Promise<Location>;

export class FieldLocation extends Blockly.Field<Location> {
  private static openDialog: LocationDialogFn | null = null;
  override SERIALIZABLE = true;

  constructor(value: Location, validator?: Blockly.FieldValidator) {
    super(value, validator);
  }

  static setOpenDialog(fn: LocationDialogFn) {
    FieldLocation.openDialog = fn;
  }

  static fromJson(options: Blockly.FieldConfig & { value?: Location }): FieldLocation {
    return new FieldLocation(options.value ?? [0, 0]);
  }

  getText() {
    const value = this.getValue();
    const location = typeof value === "string" ? JSON.parse(value) : value;
    if (!location) {
      return "位置未設定";
    }
    const [lat, lng] = location;
    return `位置 (${lat.toFixed(6)}, ${lng.toFixed(6)})`;
  }

  protected showEditor_() {
    if (!FieldLocation.openDialog) {
      console.warn('FieldLocation.openDialog is not set');
      return;
    }
    FieldLocation.openDialog(this.getValue() ?? [0, 0])
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

function geoJSONToLocation(marker: MarkerGeoJSON | null): Location | null {
  if (!marker) {
    return null;
  }
  const [lng, lat] = marker.geometry.coordinates;
  if (typeof lat !== "number" || typeof lng !== "number") {
    return null;
  }
  return [lat, lng];
}

function LocationDialog({ payload, open, onClose }: DialogProps<Location, Location>) {
  const [result, setResult] = useState(payload);
  const translate = useTranslations("Node.job.create");
  const handleChange = useCallback((marker: MarkerGeoJSON | null) => {
    setResult(geoJSONToLocation(marker) ?? [0, 0]);
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
          <MapDrawMarker
            initialMarker={{ lat: payload[0], lng: payload[1] }}
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

export function RegisterFieldLocation() {
  const dialogs = useDialogs();

  useEffect(() => {
    Blockly.fieldRegistry.register("field_location", FieldLocation);
    return () => {
      Blockly.fieldRegistry.unregister("field_location");
    };
  }, []);

  useEffect(() => {
    FieldLocation.setOpenDialog(async (currentValue: Location) => {
      return await dialogs.open(LocationDialog, currentValue);
    });
  }, [dialogs]);

  return <></>
}
