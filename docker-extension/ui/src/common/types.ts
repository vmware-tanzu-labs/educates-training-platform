// export class Workshop {
//   name: string = "";
//   url: string = "";
//   source: string = "";
//   status: string = "Unknown";
// }
// export const NullWorkshop = new Workshop();

export interface Workshop {
  name: string;
  url: string;
  source: string;
  status: string;
}

export const NullWorkshop: Workshop = {
  name: "",
  url: "",
  source: "",
  status: "",
};
