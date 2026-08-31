import React, { useState, useEffect } from "react";
import {
  Plus,
  Trash2,
  CheckCircle2,
  Circle,
  Utensils,
  ShoppingBag,
  Flame,
  X,
} from "lucide-react";
import { workspaceAPI } from "../lib/api";

interface MealEntry {
  id: string;
  name: string;
  type: "Breakfast" | "Lunch" | "Dinner" | "Snack";
  calories: number;
}

interface GroceryItem {
  id: string;
  name: string;
  completed: boolean;
}

export const FoodView: React.FC = () => {
  const [meals, setMeals] = useState<MealEntry[]>([]);
  const [groceries, setGroceries] = useState<GroceryItem[]>([]);

  const [isMealModalOpen, setIsMealModalOpen] = useState(false);
  const [mealName, setMealName] = useState("");
  const [mealType, setMealType] = useState<MealEntry["type"]>("Lunch");
  const [mealCalories, setMealCalories] = useState(500);

  const [newGroceryName, setNewGroceryName] = useState("");

  useEffect(() => {
    Promise.all([workspaceAPI.list<MealEntry>("meal"), workspaceAPI.list<GroceryItem>("grocery")])
      .then(([savedMeals, savedGroceries]) => { setMeals(savedMeals); setGroceries(savedGroceries); })
      .catch(console.error);
  }, []);

  const handleAddMeal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mealName.trim()) return;

    const payload = {
      name: mealName.trim(),
      type: mealType,
      calories: Number(mealCalories) || 0,
    };

    const newMeal = await workspaceAPI.create<MealEntry>("meal", payload);
    setMeals((prev) => [...prev, newMeal]);
    setMealName("");
    setIsMealModalOpen(false);
  };

  const deleteMeal = async (id: string) => {
    await workspaceAPI.remove("meal", id);
    setMeals((prev) => prev.filter((m) => m.id !== id));
  };

  const handleAddGrocery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGroceryName.trim()) return;

    const payload = {
      name: newGroceryName.trim(),
      completed: false,
    };

    const newItem = await workspaceAPI.create<GroceryItem>("grocery", payload);
    setGroceries((prev) => [...prev, newItem]);
    setNewGroceryName("");
  };

  const toggleGrocery = async (item: GroceryItem) => {
    const updated = await workspaceAPI.update<GroceryItem>("grocery", item.id, { completed: !item.completed });
    setGroceries((prev) => prev.map((g) => g.id === item.id ? updated : g));
  };

  const deleteGrocery = async (id: string) => {
    await workspaceAPI.remove("grocery", id);
    setGroceries((prev) => prev.filter((g) => g.id !== id));
  };

  const totalCalories = meals.reduce((acc, m) => acc + m.calories, 0);
  const calorieTarget = 2200;
  const caloriePct = Math.min(
    100,
    Math.round((totalCalories / calorieTarget) * 100),
  );

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-slate-200 select-none font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight font-sans">
            Food & Nutrition Organizer
          </h1>
          <p className="text-xs text-slate-400">
            Meal logs, calorie tracking, and grocery checklists
          </p>
        </div>
        <button
          onClick={() => setIsMealModalOpen(true)}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-accent-500 hover:bg-accent-400 text-slate-950 font-bold text-xs transition-all shadow-md shadow-accent-500/20"
        >
          <Plus size={15} strokeWidth={2.5} />
          <span>Log Meal</span>
        </button>
      </div>

      {/* Calorie Goal Summary Bar */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-sm text-white font-sans">
            <Flame size={18} className="text-molten-400" />
            <span>Today's Energy Balance</span>
          </div>
          <span className="text-slate-400">
            <strong className="text-white">{totalCalories}</strong> /{" "}
            {calorieTarget} kcal ({caloriePct}%)
          </span>
        </div>
        <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              totalCalories > calorieTarget ? "bg-danger-500" : "bg-molten-400"
            }`}
            style={{ width: `${caloriePct}%` }}
          />
        </div>
      </div>

      {/* Two Column Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Meals Column */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
              <div className="flex items-center gap-2 font-bold text-white text-sm font-sans">
                <Utensils size={16} className="text-accent-400" />
                <span>Today's Meal Log</span>
              </div>
              <span className="text-slate-500 text-[11px]">
                {meals.length} Meals
              </span>
            </div>

            {meals.length === 0 ? (
              <div className="p-8 text-center text-slate-500">
                No meals logged yet today.
              </div>
            ) : (
              <div className="space-y-2.5">
                {meals.map((m) => (
                  <div
                    key={m.id}
                    className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between hover:border-slate-700 transition-all"
                  >
                    <div>
                      <span className="text-[10px] uppercase font-bold text-accent-400 block">
                        {m.type}
                      </span>
                      <span className="text-xs text-white font-medium font-sans">
                        {m.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-slate-400 font-bold">
                        {m.calories} kcal
                      </span>
                      <button
                        onClick={() => deleteMeal(m.id)}
                        className="p-1 text-slate-500 hover:text-danger-400 transition-colors"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Grocery Checklist Column */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <div className="flex items-center gap-2 font-bold text-white text-sm font-sans">
              <ShoppingBag size={16} className="text-verdigris-400" />
              <span>Grocery Checklist</span>
            </div>
            <span className="text-slate-500 text-[11px]">
              {groceries.filter((g) => g.completed).length} / {groceries.length}{" "}
              Done
            </span>
          </div>

          <form onSubmit={handleAddGrocery} className="flex gap-2">
            <input
              type="text"
              placeholder="Add item (e.g. Eggs, Greek Yogurt)..."
              value={newGroceryName}
              onChange={(e) => setNewGroceryName(e.target.value)}
              className="flex-1 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500"
            />
            <button
              type="submit"
              className="px-3 py-1.5 rounded-xl bg-verdigris-500/20 hover:bg-verdigris-500/30 text-verdigris-400 border border-verdigris-500/40 font-bold"
            >
              Add
            </button>
          </form>

          <div className="space-y-2">
            {groceries.map((item) => (
              <div
                key={item.id}
                className={`p-2.5 rounded-xl border flex items-center justify-between transition-all ${
                  item.completed
                    ? "bg-slate-950/40 border-slate-900 opacity-50"
                    : "bg-slate-950/80 border-slate-800 hover:border-slate-700"
                }`}
              >
                <div
                  className="flex items-center gap-2.5 cursor-pointer flex-1"
                  onClick={() => toggleGrocery(item)}
                >
                  {item.completed ? (
                    <CheckCircle2 size={16} className="text-verdigris-400" />
                  ) : (
                    <Circle size={16} className="text-slate-500" />
                  )}
                  <span
                    className={`text-xs font-sans ${item.completed ? "line-through text-slate-500" : "text-white"}`}
                  >
                    {item.name}
                  </span>
                </div>
                <button
                  onClick={() => deleteGrocery(item.id)}
                  className="p-1 text-slate-500 hover:text-danger-400 transition-colors"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Add Meal Modal */}
      {isMealModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in text-xs">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h3 className="font-bold text-sm text-white font-sans">
                Log Food / Meal
              </h3>
              <button
                onClick={() => setIsMealModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleAddMeal} className="space-y-3.5">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">
                  Meal / Food Description
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Chicken Rice Bowl..."
                  value={mealName}
                  onChange={(e) => setMealName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500 font-sans"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">
                    Meal Type
                  </label>
                  <select
                    value={mealType}
                    onChange={(e) => setMealType(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500"
                  >
                    <option value="Breakfast">Breakfast</option>
                    <option value="Lunch">Lunch</option>
                    <option value="Dinner">Dinner</option>
                    <option value="Snack">Snack</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">
                    Calories (kcal)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={mealCalories}
                    onChange={(e) => setMealCalories(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsMealModalOpen(false)}
                  className="px-3 py-1.5 rounded-xl hover:bg-slate-800 text-slate-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-xl bg-accent-500 hover:bg-accent-400 text-slate-950 font-bold shadow-md"
                >
                  Log Entry
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
