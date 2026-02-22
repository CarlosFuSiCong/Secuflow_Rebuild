interface CardProps {
  variant?: string;
  extra?: string;
  children: React.ReactNode;
  default?: boolean;
  [key: string]: any;
}

function Card(props: CardProps) {
  const { variant: _variant, extra, children, default: _isDefault, ...rest } = props;

  return (
    <div
      className={`!z-5 relative flex flex-col rounded-[20px] bg-card text-card-foreground shadow-sm ${extra}`}
      {...rest}
    >
      {children}
    </div>
  );
}

export default Card;
