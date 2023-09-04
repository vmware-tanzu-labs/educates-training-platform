import * as React from "react";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import Paper from "@mui/material/Paper";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import DeleteIcon from "@mui/icons-material/Delete";
import DirectionsRunIcon from "@mui/icons-material/DirectionsRun";
import { Statuses, Workshop } from "../../common/types";
import { handleGoTo } from "../../common/goto";

// function createData(name: string, url: string, source: string, status: string) {
//   return { name, url, source, status };
// }

// const rows = [
//   createData(
//     "educates-cli--lab-k8s-fundamentals-999eff2",
//     "http://workshop.127-0-0-1.nip.io:10081",
//     "https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/latest/download/workshop.yaml",
//     "Running"
//   ),
//   createData(
//     "educates-cli--lab-k8s-fundamentals-873ded1",
//     "http://workshop.127-0-0-1.nip.io:10082",
//     "https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/latest/download/workshop.yaml",
//     "Starting"
//   ),
//   createData(
//     "educates-cli--1",
//     "http://workshop.127-0-0-1.nip.io:10082",
//     "https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/latest/download/workshop.yaml",
//     "Running"
//   ),
//   createData(
//     "educates-cli--2",
//     "http://workshop.127-0-0-1.nip.io:10082",
//     "https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/latest/download/workshop.yaml",
//     "Running"
//   ),
//   createData(
//     "educates-cli--3",
//     "http://workshop.127-0-0-1.nip.io:10082",
//     "https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/latest/download/workshop.yaml",
//     "Running"
//   ),
//   createData(
//     "educates-cli--4",
//     "http://workshop.127-0-0-1.nip.io:10082",
//     "https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/latest/download/workshop.yaml",
//     "Running"
//   ),
//   createData(
//     "educates-cli--5",
//     "http://workshop.127-0-0-1.nip.io:10082",
//     "https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/latest/download/workshop.yaml",
//     "Running"
//   ),
// ];

interface WorkshopsTableProps {
  rows: Workshop[];
  onStop: () => void;
  onOpen: () => void;
}

export default function WorkshopsTable({ rows, onStop }: WorkshopsTableProps) {
  return (
    <TableContainer component={Paper} sx={{ maxHeight: "35vh" }}>
      <Table stickyHeader sx={{ minWidth: 650 }} size="small" aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell align="center">Actions</TableCell>
            <TableCell align="center">Status</TableCell>
            <TableCell>Name</TableCell>
            <TableCell align="left">Url</TableCell>
            <TableCell align="left">Source</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.length > 0 ? (
            rows
              .sort((a, b) => (a.url < b.url ? -1 : 1))
              .map(row => (
                <TableRow
                  key={row.name}
                  sx={{ "&:last-child td, &:last-child th": { border: 0 } }}
                  selected={
                    row.status === Statuses.Starting || row.status === Statuses.Running
                      ? false
                      : true
                  }
                >
                  <TableCell align="center">
                    {row.status === Statuses.Running ? <OpenInNewIcon color="primary" /> : ""}
                    {row.status === Statuses.Running ? (
                      <DeleteIcon color="primary" onClick={() => onStop(row.name)} />
                    ) : (
                      ""
                    )}
                  </TableCell>
                  <TableCell align="center">
                    {row.status === Statuses.Starting ? (
                      <DirectionsRunIcon color="success.light" />
                    ) : (
                      ""
                    )}
                    {row.status === Statuses.Running ? <DirectionsRunIcon color="success" /> : ""}
                  </TableCell>
                  <TableCell component="th" scope="row">
                    {row.name}
                  </TableCell>
                  <TableCell align="left">
                    <Typography variant="body1">
                      <Link
                        href="#"
                        onClick={() => {
                          handleGoTo(row.url);
                        }}
                      >
                        {row.url}
                      </Link>
                    </Typography>
                    {/* <Typography>{row.url}</Typography> */}
                  </TableCell>
                  <TableCell align="left">{row.source}</TableCell>
                </TableRow>
              ))
          ) : (
            <TableRow>
              <TableCell colSpan={5} align="center">
                <Typography>No workshops</Typography>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
