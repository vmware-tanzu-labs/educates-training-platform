import * as React from "react";
import FormLabel from "@mui/material/FormLabel";
import FormControl from "@mui/material/FormControl";
import FormGroup from "@mui/material/FormGroup";
import FormControlLabel from "@mui/material/FormControlLabel";
import Switch from "@mui/material/Switch";

interface OptionsPaneProps {
  onShowPortChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  showPort: boolean;
}

export default function OptionsPane({ onShowPortChange, showPort }: OptionsPaneProps) {
  return (
    <FormControl component="fieldset" variant="standard">
      <FormGroup>
        <FormControlLabel
          control={<Switch checked={showPort} onChange={onShowPortChange} />}
          label="Show Port"
        />
      </FormGroup>
    </FormControl>
  );
}
