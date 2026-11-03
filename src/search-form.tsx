import type { FC, FormEvent } from "react";

interface SearchFormProps {
  onSearch: (params: URLSearchParams) => void;
}

const priceFields = [
  { name: "minPrice", label: "Min price" },
  { name: "maxPrice", label: "Max price" },
] as const;

export const SearchForm: FC<SearchFormProps> = ({ onSearch }) => {
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const params = new URLSearchParams();
    for (const [name, value] of new FormData(event.currentTarget)) {
      if (typeof value === "string" && value.trim()) {
        params.set(name, value.trim());
      }
    }
    onSearch(params);
  }

  return (
    <form
      aria-label="Search filters"
      className="grid grid-cols-2 items-end gap-3 sm:grid-cols-3 lg:grid-cols-4"
      onSubmit={submit}
      onReset={() => onSearch(new URLSearchParams())}
    >
      <label>
        City
        <input name="city" maxLength={120} />
      </label>
      <label>
        Keyword in description
        <input name="keyword" type="search" maxLength={250} />
      </label>
      <div className="col-span-2 grid grid-cols-2 gap-3 sm:col-span-1">
        {priceFields.map(({ name, label }) => (
          <label key={name}>
            {label}
            <input name={name} type="number" min={0} step="0.01" />
          </label>
        ))}
      </div>
      <label>
        Minimum bedrooms
        <input name="minBedrooms" type="number" min={0} step={1} />
      </label>
      <label>
        Target budget
        <input name="targetBudget" type="number" min="0.01" step="0.01" />
      </label>
      <label>
        Results per page
        <select name="pageSize" defaultValue="5">
          <option value="5">5</option>
          <option value="10">10</option>
          <option value="25">25</option>
        </select>
      </label>
      <div className="col-span-2 flex flex-wrap items-end gap-2 sm:col-span-1">
        <button type="submit" className="button-primary">Search</button>
        <button type="reset" className="button-secondary">Reset</button>
      </div>
    </form>
  );
};
