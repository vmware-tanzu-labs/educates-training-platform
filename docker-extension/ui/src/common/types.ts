// export class Workshop {
//   session: string = "";
//   url: string = "";
//   source: string = "";
//   status: string = "Unknown";
// }
// export const NullWorkshop = new Workshop();

export interface Workshop {
  session: string;
  url: string;
  source: string;
  status: string;
}

export const NullWorkshop: Workshop = {
  session: "",
  url: "",
  source: "",
  status: "",
};
