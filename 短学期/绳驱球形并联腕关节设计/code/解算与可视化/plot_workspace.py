import pandas as pd
import matplotlib.pyplot as plt


CSV_FILE = "workspace_simulation.csv"

# 最多画多少个点
MAX_FEASIBLE_POINTS = 3000
MAX_INFEASIBLE_POINTS = 3000


def sample_df(df, max_points):
    if len(df) <= max_points:
        return df
    return df.sample(n=max_points, random_state=0)


def plot_joint_space(df):
    feasible = df[df["feasible"] == 1]
    infeasible = df[df["feasible"] == 0]

    feasible_s = sample_df(feasible, MAX_FEASIBLE_POINTS)
    infeasible_s = sample_df(infeasible, MAX_INFEASIBLE_POINTS)

    fig = plt.figure(figsize=(8, 7))
    ax = fig.add_subplot(111, projection="3d")

    ax.scatter(
        infeasible_s["theta1_deg"],
        infeasible_s["theta2_deg"],
        infeasible_s["theta3_deg"],
        s=5,
        c="lightgray",
        alpha=0.25,
        label=f"infeasible sample ({len(infeasible_s)})",
    )

    ax.scatter(
        feasible_s["theta1_deg"],
        feasible_s["theta2_deg"],
        feasible_s["theta3_deg"],
        s=8,
        c="tab:blue",
        alpha=0.75,
        label=f"feasible sample ({len(feasible_s)})",
    )

    ax.set_xlabel("theta1 deg")
    ax.set_ylabel("theta2 deg")
    ax.set_zlabel("theta3 deg")
    ax.set_title("Joint-Space Workspace Sample")
    ax.legend()

    plt.tight_layout()


def plot_orientation_space(df):
    feasible = df[df["feasible"] == 1].dropna(
        subset=["yaw_deg", "pitch_deg", "roll_deg"]
    )

    feasible_s = sample_df(feasible, MAX_FEASIBLE_POINTS)

    fig = plt.figure(figsize=(8, 7))
    ax = fig.add_subplot(111, projection="3d")

    sc = ax.scatter(
        feasible_s["yaw_deg"],
        feasible_s["pitch_deg"],
        feasible_s["roll_deg"],
        s=8,
        c=feasible_s["zeta"],
        cmap="viridis",
        alpha=0.85,
    )

    ax.set_xlabel("yaw deg")
    ax.set_ylabel("pitch deg")
    ax.set_zlabel("roll deg")
    ax.set_title(f"Orientation-Space Feasible Sample ({len(feasible_s)} points)")

    plt.colorbar(sc, ax=ax, shrink=0.7, label="zeta")
    plt.tight_layout()


def plot_message_count(df):
    counts = df["message"].value_counts()

    fig = plt.figure(figsize=(9, 4))
    counts.plot(kind="bar", color="tab:orange")
    plt.xlabel("message")
    plt.ylabel("count")
    plt.title("Result Message Counts")
    plt.xticks(rotation=30, ha="right")
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()

    print("Message counts:")
    print(counts)


def main():
    df = pd.read_csv(CSV_FILE)

    print("Total points:", len(df))
    print("Feasible points:", int(df["feasible"].sum()))
    print("Feasible ratio:", df["feasible"].mean())

    plot_joint_space(df)
    plot_orientation_space(df)
    plot_message_count(df)

    plt.show()


if __name__ == "__main__":
    main()
