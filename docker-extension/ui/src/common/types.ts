// export class Workshop {
//   workshopDefinitionURL: string = "";
//   name: string = "";
//   running: boolean = false;
//   workshopUrl: string = "";
// }
// export const NullWorkshop = new Workshop();

export interface Workshop {
  workshopDefinitionURL: string;
  name: string;
  running: boolean;
  workshopUrl: string;
}

export const NullWorkshop: Workshop = {
  workshopDefinitionURL: "",
  name: "",
  running: false,
  workshopUrl: "",
};
