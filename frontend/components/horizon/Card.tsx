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
      className={`relative flex flex-col rounded border border-border bg-card text-card-foreground ${extra ?? ""}`}
      {...rest}
    >
      {children}
    </div>
  );
}

export default Card;
