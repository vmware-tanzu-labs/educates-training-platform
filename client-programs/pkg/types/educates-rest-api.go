package types

type WorkshopsCatalogResponse struct {
	Portal         PortalDetails        `json:"portal"`
	Environonments []EnvironmentDetails `json:"environments"`
}

type PortalDetails struct {
	Name string `json:"name"`
	// Labels     []string         `json:"labels"`
	UID        string         `json:"uid"`
	Generation int64          `json:"generation"`
	URL        string         `json:"url"`
	Sessions   SessionDetails `json:"sessions"`
}

type SessionDetails struct {
	Maximum    int64 `json:"maximum"`
	Registered int64 `json:"registered"`
	Anonymous  int64 `json:"anonymous"`
	Allocated  int64 `json:"allocated"`
}

type WorkshopDetails struct {
	Name        string   `json:"name"`
	Title       string   `json:"title"`
	Description string   `json:"description"`
	Vendor      string   `json:"vendor"`
	Authors     []string `json:"authors"`
	Difficulty  string   `json:"difficulty"`
	Duration    string   `json:"duration"`
	Tags        []string `json:"tags"`
	// Labels      []string `json:"labels"`
	Logo string `json:"logo"`
	URL  string `json:"url"`
}

type EnvironmentDetails struct {
	Name      string          `json:"name"`
	State     string          `json:"state"`
	Duration  int64           `json:"duration"`
	Capacity  int64           `json:"capacity"`
	Reserved  int64           `json:"reserved"`
	Allocated int64           `json:"allocated"`
	Available int64           `json:"available"`
	Workshop  WorkshopDetails `json:"workshop"`
}
