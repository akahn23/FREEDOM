/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from "react";
import { useFormContext, useFieldArray } from "react-hook-form";
import { useTranslations } from "next-intl";
import dynamic from "next/dynamic";
import { Button, Stack, Typography, Dialog, DialogActions, DialogTitle, DialogContent } from "@mui/material";
import { Close, Map } from '@mui/icons-material';
import { useDialogs, DialogProps } from "@toolpad/core/useDialogs";
import { IntersectionFormResponse } from "@/types/config";
import { FormProps } from "@/components/config/forms";

const MapView = dynamic(() => import("@/components/map/MapView"), { ssr: false });
const IntersectionDraw = dynamic(() => import("@/components/map/IntersectionDraw"), { ssr: false });

/** 地図ダイアログ */
function IntersectionDialog({ open, onClose, name, setValue, getValues }: DialogProps<{}> & { name: string; setValue: any; getValues: any }) {
  const initialData = getValues(name) || { entry_area: [], reserve_area: [] };
  const [tempShapes, setTempShapes] = useState<{ entryShapes: any[]; reserveShapes: any[] }>({
    entryShapes: [],
    reserveShapes: []
  });
  const translate = useTranslations("Config");

  // GeoJSON → backend形式に変換
  const convertShapesToAreas = (shapes: any[]) => {
    return shapes.map(shape => ({
      name: shape.properties.name,
      vertex_list: shape.geometry.coordinates[0].map(([lng, lat]: [number, number]) => [lat, lng]),
      priority: shape.properties.priority
    }));
  };

  return (
    <Dialog fullWidth maxWidth="lg" open={open} onClose={() => {
      setValue(name, {
        entry_area: convertShapesToAreas(tempShapes.entryShapes),
        reserve_area: convertShapesToAreas(tempShapes.reserveShapes)
      }, { shouldDirty: true });
      onClose();
    }}>
      <DialogTitle>{translate("intersection.intersectionTitle")}</DialogTitle>
      <DialogContent sx={{ height: "80vh", padding: 0 }}>
        <MapView style={{ width: "100%", height: "100%" }}>
          <IntersectionDraw
            onChange={setTempShapes}
            initialShapes={initialData}
          />
        </MapView>
      </DialogContent>
      <DialogActions sx={{ justifyContent: "flex-end", padding: "8px 16px" }}>
        <Button
          variant="outlined"
          color="primary"
          startIcon={<Close />}
          onClick={() => {
            setValue(name, {
              entry_area: convertShapesToAreas(tempShapes.entryShapes),
              reserve_area: convertShapesToAreas(tempShapes.reserveShapes)
            }, { shouldDirty: true });
            onClose();
          }}
        >
          {translate("dialog.close")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

/**
 * エリアフォーム
 * @param name 設定名
 * @param form 設定内容
 * @param disabled 無効
 * @param validate 検証イベント
 */
export default function MapImageForm({ name, form }: FormProps<IntersectionFormResponse>) {
  const { control, getValues, setValue } = useFormContext();
  useFieldArray({
    control,
    name: name,
  });
  const translate = useTranslations("Config");
  const dialog = useDialogs();

  //  entry_area と reserve_area の数を取得
  const areas = getValues(name) || { entry_area: [], reserve_area: [] };

  return (
    <Stack direction="row" spacing={1}  sx={{ justifyContent: "flex-start", alignItems: "center" }}>
      <Button
        component="label"
        variant="outlined"
        startIcon={<Map/>}
        onClick={() => dialog.open((props) => <IntersectionDialog {...props} name={name} setValue={setValue} getValues={getValues} />, {})}
      >
        {form.label}
      </Button>
      <Typography sx={{ whiteSpace: 'pre-line' }}>
        {translate("intersection.text", { entryNum: areas.entry_area?.length || 0, reserveNum: areas.reserve_area?.length || 0 })}
      </Typography>
    </Stack>
  );
}
