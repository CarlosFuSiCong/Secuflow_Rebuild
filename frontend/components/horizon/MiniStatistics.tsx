import React from "react";

interface MiniStatisticsProps {
  name: string;
  value: string | number;
  icon: React.ReactNode;
  iconBg?: string;
}

function MiniStatistics(props: MiniStatisticsProps) {
  const { name, value, icon, iconBg } = props;
  return (
    <div className="flex w-full items-center gap-3 rounded-[20px] bg-card px-[18px] py-4 shadow-sm">
      <div
        className={`flex h-[56px] w-14 items-center justify-center rounded-full text-[33px] text-primary ${iconBg} `}
      >
        {icon}
      </div>
      <div className="">
        <p className=" mb-1 text-sm font-medium text-muted-foreground">{name}</p>
        <h3 className="text-xl font-bold leading-6 text-foreground">
          {value}
        </h3>
      </div>
    </div>
  );
}

export default MiniStatistics;
